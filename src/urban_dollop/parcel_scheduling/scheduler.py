import tomllib
from pathlib import Path

import numpy as np

from urban_dollop.helpers.validation import validate_depot_zones
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
    validate_depot_zones(depots, skim)

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

        # Split demands into vehicle-capacity tours using spatial clustering
        tours = _cluster_demands_spatially(depot_demands, depot.zone_id, max_capacity, skim)

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


def _cluster_demands_spatially(
    demands: list[ParcelDemand],
    depot_zone_id: int,
    max_capacity: int,
    skim: SkimMatrix,
) -> list[list[ParcelDemand]]:
    """Cluster demands into capacity-constrained tours using MASS-GT spatial clustering.

    Demands whose parcel count meets or exceeds max_capacity are assigned
    dedicated full-load tours. Remaining demands are clustered iteratively:
    the furthest unassigned demand (by travel time from the depot) seeds each
    new cluster; the nearest unassigned demands to that seed are greedily added
    until capacity is reached.
    """
    tours: list[list[ParcelDemand]] = []
    to_cluster: list[ParcelDemand] = []

    for d in demands:
        if d.n_parcels >= max_capacity:
            tours.append([d])
        else:
            to_cluster.append(d)

    if not to_cluster:
        return tours

    # Furthest-from-depot first; this order seeds each new cluster
    to_cluster.sort(
        key=lambda d: skim.get(depot_zone_id, d.destination_zone_id),
        reverse=True,
    )
    unassigned = list(to_cluster)

    while unassigned:
        seed = unassigned.pop(0)
        cluster = [seed]
        load = seed.n_parcels

        # Sort remaining by proximity to seed (nearest first)
        unassigned.sort(
            key=lambda d: skim.get(seed.destination_zone_id, d.destination_zone_id)
        )

        leftover: list[ParcelDemand] = []
        for d in unassigned:
            if load + d.n_parcels <= max_capacity:
                cluster.append(d)
                load += d.n_parcels
            else:
                leftover.append(d)

        # Restore furthest-first ordering for the next seed selection
        leftover.sort(
            key=lambda d: skim.get(depot_zone_id, d.destination_zone_id),
            reverse=True,
        )
        unassigned = leftover
        tours.append(cluster)

    return tours


def _nearest_neighbour(
    depot_zone_id: int,
    stops: list[ParcelDemand],
    skim: SkimMatrix,
) -> list[ParcelDemand]:
    """Build a tour by always visiting the nearest unvisited stop."""
    # depot at local index 0, stops at 1..n
    zone_ids = [depot_zone_id] + [s.destination_zone_id for s in stops]
    sub = skim.submatrix(zone_ids)

    remaining = list(range(1, len(stops) + 1))  # local indices
    ordered_local: list[int] = []
    current = 0  # depot

    while remaining:
        best = int(np.argmin(sub[current, remaining]))
        current = remaining[best]
        ordered_local.append(current)
        remaining.pop(best)

    return [stops[idx - 1] for idx in ordered_local]


def _two_opt(
    depot_zone_id: int,
    stops: list[ParcelDemand],
    skim: SkimMatrix,
    max_passes: int = 10,
) -> list[ParcelDemand]:
    """Improve a tour with 2-opt swaps; stops after max_passes or convergence."""
    if len(stops) < 3:
        return stops

    # depot at local index 0, stops at 1..n — build sub-matrix once
    zone_ids = [depot_zone_id] + [s.destination_zone_id for s in stops]
    sub = skim.submatrix(zone_ids)

    n = len(stops)
    route = np.arange(1, n + 1, dtype=np.intp)  # local indices, depot=0

    for _ in range(max_passes):
        improved = False
        for i in range(n - 1):
            a = route[i - 1] if i > 0 else 0
            b = route[i]
            ab = sub[a, b]
            for j in range(i + 2, n):
                c = route[j]
                d = route[j + 1] if j + 1 < n else 0
                if sub[a, c] + sub[b, d] < ab + sub[c, d] - 1e-6:
                    route[i : j + 1] = route[i : j + 1][::-1]
                    b = route[i]
                    ab = sub[a, b]
                    improved = True
        if not improved:
            break

    return [stops[idx - 1] for idx in route]


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
