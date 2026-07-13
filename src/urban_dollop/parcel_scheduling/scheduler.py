import math
import tomllib
from pathlib import Path
from typing import Callable

import numpy as np

from urban_dollop.helpers.validation import validate_origin_zones
from urban_dollop.models.delivery_trip import DeliveryTrip
from urban_dollop.models.parcel_demand import ParcelDemand
from urban_dollop.models.skim_distance import SkimDistance
from urban_dollop.models.vehicle import Vehicle
from urban_dollop.models.zone import Zone
from urban_dollop.parcel_scheduling.config import ParcelSchedulingConfig


def schedule_parcel_deliveries(
    demands: list[ParcelDemand],
    vehicles: list[Vehicle],
    skim_distance: SkimDistance,
    zones: list[Zone],
    config: ParcelSchedulingConfig | None = None,
) -> list[DeliveryTrip]:
    """Convert aggregated parcel demand into delivery trips.

    For each (origin zone, carrier) pair, groups demand zones into
    vehicle-capacity-constrained tours using nearest-neighbour construction
    followed by 2-opt improvement. Each tour becomes a sequence of
    DeliveryTrip legs: origin→stop₁, stop₁→stop₂, …, stopₙ→origin.

    Spatial clustering uses distance (not travel time) with an optional
    Euclidean blend when zone centroids are available, matching the
    MASS-GT clustering heuristic. Tour construction and improvement use
    distance only. 2-opt is used instead of MASS-GT's pairwise location
    swaps — see literate-fishstick for justification.

    Args:
        demands: Output of generate_parcel_demand(), generate_logit_demand(),
            or a consolidation module.
        vehicles: Available vehicle types sorted by capacity (ascending).
            The smallest vehicle whose max_parcels ≥ tour size is chosen.
        skim_distance: Travel-distance matrix used for clustering and tour
            optimisation.
        zones: All zones in the scenario. Centroid coordinates (x, y) are
            used for Euclidean blending in clustering when present. Load
            zones from a GeoPackage to get centroids automatically; CSV
            zones or programmatically constructed zones skip the blend.
        config: Optional overrides; falls back to urban-dollop.toml then defaults.

    Returns:
        List of DeliveryTrip records in (tour_id, trip_id) order.
    """
    config = _resolve_config(config)
    validate_origin_zones(demands, skim_distance)

    rng = np.random.default_rng(config.seed)
    dist = config.departure_time_distribution

    zone_coords: dict[int, tuple[float, float]] = {
        z.zone_id: (z.x, z.y)
        for z in zones
        if z.x is not None and z.y is not None
    }
    cluster_dist_fn = _make_cluster_distance(skim_distance, zone_coords)

    vehicles_sorted = sorted(vehicles, key=lambda v: v.max_parcels)
    max_capacity = vehicles_sorted[-1].max_parcels

    by_origin: dict[tuple[int, str], list[ParcelDemand]] = {}
    for d in demands:
        by_origin.setdefault((d.origin_zone_id, d.carrier), []).append(d)

    trips: list[DeliveryTrip] = []
    tour_id = 0

    for (origin_zone_id, carrier), group_demands in by_origin.items():
        tours = _cluster_demands_spatially(
            group_demands, origin_zone_id, max_capacity, cluster_dist_fn
        )

        for stop_list in tours:
            tour_id += 1
            vehicle = _select_vehicle(
                sum(d.n_parcels for d in stop_list), vehicles_sorted
            )
            departure_hour = _sample_hour(dist, rng) if dist is not None else None

            ordered = _nearest_neighbour(origin_zone_id, stop_list, skim_distance)
            ordered = _two_opt(origin_zone_id, ordered, skim_distance)

            origin = origin_zone_id
            for trip_id, stop in enumerate(ordered, start=1):
                trips.append(
                    DeliveryTrip(
                        tour_id=tour_id,
                        trip_id=trip_id,
                        carrier=carrier,
                        origin_zone_id=origin,
                        destination_zone_id=stop.destination_zone_id,
                        n_parcels=stop.n_parcels,
                        vehicle_id=vehicle.vehicle_id,
                        departure_hour=departure_hour,
                    )
                )
                origin = stop.destination_zone_id

            trips.append(
                DeliveryTrip(
                    tour_id=tour_id,
                    trip_id=len(ordered) + 1,
                    carrier=carrier,
                    origin_zone_id=origin,
                    destination_zone_id=origin_zone_id,
                    n_parcels=0,
                    vehicle_id=vehicle.vehicle_id,
                    departure_hour=departure_hour,
                )
            )

    return trips


def _make_cluster_distance(
    skim: SkimDistance,
    zone_coords: dict[int, tuple[float, float]],
) -> Callable[[int, int], float]:
    """Return a distance callable for spatial clustering.

    When zone centroids are available, returns a blended metric
    norm(skim_distance) + norm(euclidean), matching MASS-GT's
    skimClustering formulation. Falls back to raw skim distance
    when centroids are absent.
    """
    if not zone_coords:
        return skim.get

    max_skim = float(skim.data.max()) or 1.0

    coords_list = list(zone_coords.values())
    if len(coords_list) >= 2:
        xs = np.array([c[0] for c in coords_list])
        ys = np.array([c[1] for c in coords_list])
        dx = xs[:, None] - xs[None, :]
        dy = ys[:, None] - ys[None, :]
        max_euclid = float(np.sqrt(dx**2 + dy**2).max()) or 1.0
    else:
        max_euclid = 1.0

    def blended(from_id: int, to_id: int) -> float:
        d = skim.get(from_id, to_id) / max_skim
        if from_id in zone_coords and to_id in zone_coords:
            x1, y1 = zone_coords[from_id]
            x2, y2 = zone_coords[to_id]
            e = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2) / max_euclid
        else:
            e = 0.0
        return d + e

    return blended


def _cluster_demands_spatially(
    demands: list[ParcelDemand],
    origin_zone_id: int,
    max_capacity: int,
    dist_fn: Callable[[int, int], float],
) -> list[list[ParcelDemand]]:
    """Cluster demands into capacity-constrained tours.

    Demands whose parcel count meets or exceeds max_capacity are assigned
    dedicated full-load tours. Remaining demands are clustered iteratively:
    the furthest unassigned demand seeds each new cluster; the nearest
    unassigned demands to that seed are greedily added until capacity is
    reached. dist_fn provides the distance metric (blended or raw).
    """
    tours: list[list[ParcelDemand]] = []
    to_cluster: list[ParcelDemand] = []

    for d in demands:
        if d.n_parcels > max_capacity:
            raise ValueError(
                f"Demand record ({d.origin_zone_id} → {d.destination_zone_id}, "
                f"carrier={d.carrier!r}) has n_parcels={d.n_parcels} which exceeds "
                f"the largest vehicle capacity ({max_capacity}). "
                "Split the demand or add a larger vehicle."
            )
        if d.n_parcels >= max_capacity:
            tours.append([d])
        else:
            to_cluster.append(d)

    if not to_cluster:
        return tours

    to_cluster.sort(
        key=lambda d: dist_fn(origin_zone_id, d.destination_zone_id),
        reverse=True,
    )
    unassigned = list(to_cluster)

    while unassigned:
        seed = unassigned.pop(0)
        cluster = [seed]
        load = seed.n_parcels

        unassigned.sort(
            key=lambda d: dist_fn(seed.destination_zone_id, d.destination_zone_id)
        )

        leftover: list[ParcelDemand] = []
        for d in unassigned:
            if load + d.n_parcels <= max_capacity:
                cluster.append(d)
                load += d.n_parcels
            else:
                leftover.append(d)

        leftover.sort(
            key=lambda d: dist_fn(origin_zone_id, d.destination_zone_id),
            reverse=True,
        )
        unassigned = leftover
        tours.append(cluster)

    return tours


def _nearest_neighbour(
    origin_zone_id: int,
    stops: list[ParcelDemand],
    skim: SkimDistance,
) -> list[ParcelDemand]:
    """Build a tour by always visiting the nearest unvisited stop."""
    zone_ids = [origin_zone_id] + [s.destination_zone_id for s in stops]
    sub = skim.submatrix(zone_ids)

    remaining = list(range(1, len(stops) + 1))
    ordered_local: list[int] = []
    current = 0

    while remaining:
        best = int(np.argmin(sub[current, remaining]))
        current = remaining[best]
        ordered_local.append(current)
        remaining.pop(best)

    return [stops[idx - 1] for idx in ordered_local]


def _two_opt(
    origin_zone_id: int,
    stops: list[ParcelDemand],
    skim: SkimDistance,
    max_passes: int = 10,
) -> list[ParcelDemand]:
    """Improve a tour with 2-opt swaps; stops after max_passes or convergence."""
    if len(stops) < 3:
        return stops

    zone_ids = [origin_zone_id] + [s.destination_zone_id for s in stops]
    sub = skim.submatrix(zone_ids)

    n = len(stops)
    route = np.arange(1, n + 1, dtype=np.intp)

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


def _sample_hour(dist: list[float], rng: np.random.Generator) -> int:
    """Sample a departure hour from a 24-value cumulative distribution."""
    return int(min(np.searchsorted(dist, rng.random()), 23))


def _resolve_config(config: ParcelSchedulingConfig | None) -> ParcelSchedulingConfig:
    toml_data: dict = {}
    toml_path = Path("urban-dollop.toml")
    if toml_path.exists():
        with open(toml_path, "rb") as f:
            toml_data = tomllib.load(f).get("parcel_scheduling", {})

    if config is not None:
        toml_data.update(config.model_dump(exclude_none=True))

    return ParcelSchedulingConfig(**toml_data)
