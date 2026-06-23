from itertools import groupby

import pytest

from urban_dollop import generate_parcel_demand, schedule_parcel_deliveries
from urban_dollop.models.parcel_demand import ParcelDemand
from urban_dollop.parcel_scheduling.config import ParcelSchedulingConfig


def test_total_parcels_preserved(
    zones, depots, carriers, vehicles, skim, skim_distance, demand_config
):
    demands = generate_parcel_demand(zones, depots, carriers, skim, demand_config)
    trips = schedule_parcel_deliveries(demands, vehicles, skim_distance, zones)
    assert sum(t.n_parcels for t in trips) == sum(d.n_parcels for d in demands)


def test_each_tour_has_exactly_one_return_leg(
    zones, depots, carriers, vehicles, skim, skim_distance, demand_config
):
    demands = generate_parcel_demand(zones, depots, carriers, skim, demand_config)
    trips = schedule_parcel_deliveries(demands, vehicles, skim_distance, zones)
    n_tours = len({t.tour_id for t in trips})
    return_legs = [t for t in trips if t.n_parcels == 0]
    assert len(return_legs) == n_tours


def test_trip_ids_are_sequential_per_tour(
    zones, depots, carriers, vehicles, skim, skim_distance, demand_config
):
    demands = generate_parcel_demand(zones, depots, carriers, skim, demand_config)
    trips = schedule_parcel_deliveries(
        demands, vehicles, skim_distance, zones, ParcelSchedulingConfig(seed=0)
    )
    for _, legs in groupby(trips, key=lambda t: t.tour_id):
        ids = [t.trip_id for t in legs]
        assert ids == list(range(1, len(ids) + 1))


def test_all_vehicle_ids_are_valid(
    zones, depots, carriers, vehicles, skim, skim_distance, demand_config
):
    valid_ids = {v.vehicle_id for v in vehicles}
    demands = generate_parcel_demand(zones, depots, carriers, skim, demand_config)
    trips = schedule_parcel_deliveries(demands, vehicles, skim_distance, zones)
    assert all(t.vehicle_id in valid_ids for t in trips)


def test_all_origin_zones_are_depot_zones(
    zones, depots, carriers, vehicles, skim, skim_distance, demand_config
):
    depot_zones = {d.zone_id for d in depots}
    demands = generate_parcel_demand(zones, depots, carriers, skim, demand_config)
    trips = schedule_parcel_deliveries(demands, vehicles, skim_distance, zones)
    first_legs = [t for t in trips if t.trip_id == 1]
    assert all(t.origin_zone_id in depot_zones for t in first_legs)


def test_raises_for_origin_zone_not_in_skim(zones, vehicles, skim_distance):
    bad_demands = [
        ParcelDemand(origin_zone_id=9999, destination_zone_id=1, carrier="alpha", n_parcels=10)
    ]
    with pytest.raises(ValueError, match="not present in the skim"):
        schedule_parcel_deliveries(bad_demands, vehicles, skim_distance, zones)


def test_empty_demands_produces_no_trips(zones, vehicles, skim_distance):
    trips = schedule_parcel_deliveries([], vehicles, skim_distance, zones)
    assert trips == []


def test_no_tour_exceeds_vehicle_capacity(
    zones, depots, carriers, vehicles, skim, skim_distance, demand_config
):
    demands = generate_parcel_demand(zones, depots, carriers, skim, demand_config)
    trips = schedule_parcel_deliveries(demands, vehicles, skim_distance, zones)
    vehicle_capacity = {v.vehicle_id: v.max_parcels for v in vehicles}
    tour_load: dict[int, int] = {}
    tour_vehicle: dict[int, int] = {}
    for t in trips:
        tour_load[t.tour_id] = tour_load.get(t.tour_id, 0) + t.n_parcels
        tour_vehicle[t.tour_id] = t.vehicle_id
    for tour_id, load in tour_load.items():
        assert load <= vehicle_capacity[tour_vehicle[tour_id]]


def test_all_stops_in_tour_share_carrier(
    zones, depots, carriers, vehicles, skim, skim_distance, demand_config
):
    demands = generate_parcel_demand(zones, depots, carriers, skim, demand_config)
    trips = schedule_parcel_deliveries(demands, vehicles, skim_distance, zones)
    tour_carriers: dict[int, set[str]] = {}
    for t in trips:
        tour_carriers.setdefault(t.tour_id, set()).add(t.carrier)
    assert all(len(cs) == 1 for cs in tour_carriers.values())
