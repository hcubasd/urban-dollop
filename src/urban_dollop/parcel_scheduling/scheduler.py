import tomllib
from pathlib import Path

import numpy as np

from urban_dollop.models.delivery_trip import DeliveryTrip
from urban_dollop.models.depot import Depot
from urban_dollop.models.parcel_demand import ParcelDemand
from urban_dollop.models.skim_matrix import SkimMatrix
from urban_dollop.models.vehicle import Vehicle
from urban_dollop.parcel_scheduling.config import ParcelSchedulingConfig


def schedule_parcel_deliveries(
    demands: list[ParcelDemand],
    depots: list[Depot],
    vehicles: list[Vehicle],
    skim: SkimMatrix,
    config: ParcelSchedulingConfig | None = None,
) -> list[DeliveryTrip]:
    """Convert aggregated parcel demand into delivery trips.

    For each depot, groups demand zones into vehicle-capacity-constrained tours
    using nearest-neighbour construction followed by 2-opt improvement. Each
    tour becomes a sequence of DeliveryTrip legs: depot→stop₁, stop₁→stop₂,
    …, stopₙ→depot.

    Args:
        demands: Output of generate_parcel_demand().
        depots: Depot registry; used to look up carrier and zone_id per depot.
        vehicles: Available vehicle types sorted by capacity (ascending).
            The largest vehicle whose max_parcels ≥ tour size is chosen.
        skim: Travel-time matrix used for nearest-neighbour and 2-opt.
        config: Optional overrides; falls back to urban-dollop.toml then defaults.

    Returns:
        List of DeliveryTrip records in (tour_id, trip_id) order.
    """
    config = _resolve_config(config)
    rng = np.random.default_rng(config.seed)

    depot_map: dict[int, Depot] = {d.depot_id: d for d in depots}
    vehicles_sorted = sorted(vehicles, key=lambda v: v.max_parcels)
    max_capacity = vehicles_sorted[-1].max_parcels

    # Group demands by depot
    by_depot: dict[int, list[ParcelDemand]] = {}
    for d in demands:
        by_depot.setdefault(d.depot_id, []).append(d)

    trips: list[DeliveryTrip] = []
    tour_id = 0

    for depot_id, depot_demands in by_depot.items():
        depot = depot_map[depot_id]

        # Split demands into vehicle-capacity tours
        tours = _build_tours(depot_demands, max_capacity, rng)

        for stop_list in tours:
            tour_id += 1
            vehicle = _select_vehicle(
                sum(d.n_parcels for d in stop_list), vehicles_sorted
            )

            # Nearest-neighbour tour from depot
            ordered = _nearest_neighbour(depot.zone_id, stop_list, skim)
            # 2-opt improvement
            ordered = _two_opt(depot.zone_id, ordered, skim)

            # Emit trip legs
            origin = depot.zone_id
            for trip_id, stop in enumerate(ordered, start=1):
                trips.append(
                    DeliveryTrip(
                        tour_id=tour_id,
                        trip_id=trip_id,
                        depot_id=depot_id,
                        carrier=depot.carrier,
                        origin_zone_id=origin,
                        destination_zone_id=stop.destination_zone_id,
                        n_parcels=stop.n_parcels,
                        vehicle_id=vehicle.vehicle_id,
                    )
                )
                origin = stop.destination_zone_id

            # Return leg: last stop → depot
            trips.append(
                DeliveryTrip(
                    tour_id=tour_id,
                    trip_id=len(ordered) + 1,
                    depot_id=depot_id,
                    carrier=depot.carrier,
                    origin_zone_id=origin,
                    destination_zone_id=depot.zone_id,
                    n_parcels=0,
                    vehicle_id=vehicle.vehicle_id,
                )
            )

    return trips


def _build_tours(
    demands: list[ParcelDemand],
    max_capacity: int,
    rng: np.random.Generator,
) -> list[list[ParcelDemand]]:
    """Pack demands into tours respecting max_capacity using a greedy bin-packer."""
    # Shuffle for randomness when seed is set; preserves reproducibility
    order = rng.permutation(len(demands))
    shuffled = [demands[i] for i in order]

    tours: list[list[ParcelDemand]] = []
    current_tour: list[ParcelDemand] = []
    current_load = 0

    for demand in shuffled:
        if current_load + demand.n_parcels > max_capacity and current_tour:
            tours.append(current_tour)
            current_tour = []
            current_load = 0
        current_tour.append(demand)
        current_load += demand.n_parcels

    if current_tour:
        tours.append(current_tour)

    return tours


def _nearest_neighbour(
    depot_zone_id: int,
    stops: list[ParcelDemand],
    skim: SkimMatrix,
) -> list[ParcelDemand]:
    """Build a tour by always visiting the nearest unvisited stop."""
    remaining = list(stops)
    ordered: list[ParcelDemand] = []
    current = depot_zone_id

    while remaining:
        times = [skim.get(current, s.destination_zone_id) for s in remaining]
        idx = int(np.argmin(times))
        ordered.append(remaining.pop(idx))
        current = ordered[-1].destination_zone_id

    return ordered


def _two_opt(
    depot_zone_id: int,
    stops: list[ParcelDemand],
    skim: SkimMatrix,
    max_passes: int = 10,
) -> list[ParcelDemand]:
    """Improve a tour with 2-opt swaps; stops after max_passes or convergence."""
    if len(stops) < 3:
        return stops

    route = list(stops)

    for _ in range(max_passes):
        improved = False
        for i in range(len(route) - 1):
            for j in range(i + 2, len(route)):
                # Current: ...→route[i]→route[i+1]→...→route[j]→...
                # Swap:    ...→route[i]→route[j]→...→route[i+1]→...
                a = route[i - 1].destination_zone_id if i > 0 else depot_zone_id
                b = route[i].destination_zone_id
                c = route[j].destination_zone_id
                d = (
                    route[j + 1].destination_zone_id
                    if j + 1 < len(route)
                    else depot_zone_id
                )

                before = skim.get(a, b) + skim.get(c, d)
                after = skim.get(a, c) + skim.get(b, d)

                if after < before - 1e-6:
                    route[i : j + 1] = route[i : j + 1][::-1]
                    improved = True

        if not improved:
            break

    return route


def _select_vehicle(n_parcels: int, vehicles_sorted: list[Vehicle]) -> Vehicle:
    """Return the smallest vehicle that fits n_parcels; fall back to largest."""
    for v in vehicles_sorted:
        if v.max_parcels >= n_parcels:
            return v
    return vehicles_sorted[-1]


def _resolve_config(config: ParcelSchedulingConfig | None) -> ParcelSchedulingConfig:
    toml_data: dict = {}
    toml_path = Path("urban-dollop.toml")
    if toml_path.exists():
        with open(toml_path, "rb") as f:
            toml_data = tomllib.load(f).get("parcel_scheduling", {})

    if config is not None:
        toml_data.update(config.model_dump(exclude_none=True))

    return ParcelSchedulingConfig(**toml_data)
