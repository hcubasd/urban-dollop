from itertools import groupby

import pytest

from urban_dollop import generate_parcel_demand, schedule_parcel_deliveries
from urban_dollop.models.depot import Depot
from urban_dollop.parcel_scheduling.config import ParcelSchedulingConfig


def test_total_parcels_preserved(zones, depots, carriers, vehicles, skim, demand_config):
    demands = generate_parcel_demand(zones, depots, carriers, skim, demand_config)
    trips = schedule_parcel_deliveries(demands, depots, vehicles, skim)
    assert sum(t.n_parcels for t in trips) == sum(d.n_parcels for d in demands)


def test_each_tour_has_exactly_one_return_leg(zones, depots, carriers, vehicles, skim, demand_config):
    demands = generate_parcel_demand(zones, depots, carriers, skim, demand_config)
    trips = schedule_parcel_deliveries(demands, depots, vehicles, skim)
    n_tours = len({t.tour_id for t in trips})
    return_legs = [t for t in trips if t.n_parcels == 0]
    assert len(return_legs) == n_tours


def test_trip_ids_are_sequential_per_tour(zones, depots, carriers, vehicles, skim, demand_config):
    demands = generate_parcel_demand(zones, depots, carriers, skim, demand_config)
    trips = schedule_parcel_deliveries(demands, depots, vehicles, skim, ParcelSchedulingConfig(seed=0))
    for _, legs in groupby(trips, key=lambda t: t.tour_id):
        ids = [t.trip_id for t in legs]
        assert ids == list(range(1, len(ids) + 1))


def test_all_vehicle_ids_are_valid(zones, depots, carriers, vehicles, skim, demand_config):
    valid_ids = {v.vehicle_id for v in vehicles}
    demands = generate_parcel_demand(zones, depots, carriers, skim, demand_config)
    trips = schedule_parcel_deliveries(demands, depots, vehicles, skim)
    assert all(t.vehicle_id in valid_ids for t in trips)


def test_all_depot_ids_are_valid(zones, depots, carriers, vehicles, skim, demand_config):
    valid_ids = {d.depot_id for d in depots}
    demands = generate_parcel_demand(zones, depots, carriers, skim, demand_config)
    trips = schedule_parcel_deliveries(demands, depots, vehicles, skim)
    assert all(t.depot_id in valid_ids for t in trips)


def test_raises_for_depot_zone_not_in_skim(zones, depots, carriers, vehicles, skim, demand_config):
    demands = generate_parcel_demand(zones, depots, carriers, skim, demand_config)
    bad_depots = depots + [Depot(depot_id=99, carrier="alpha", zone_id=9999)]
    with pytest.raises(ValueError, match="not present in the skim"):
        schedule_parcel_deliveries(demands, bad_depots, vehicles, skim)


def test_empty_demands_produces_no_trips(zones, depots, carriers, vehicles, skim):
    trips = schedule_parcel_deliveries([], depots, vehicles, skim)
    assert trips == []


def test_no_tour_exceeds_vehicle_capacity(zones, depots, carriers, vehicles, skim, demand_config):
    demands = generate_parcel_demand(zones, depots, carriers, skim, demand_config)
    trips = schedule_parcel_deliveries(demands, depots, vehicles, skim)
    vehicle_capacity = {v.vehicle_id: v.max_parcels for v in vehicles}
    tour_load: dict[int, int] = {}
    tour_vehicle: dict[int, int] = {}
    for t in trips:
        tour_load[t.tour_id] = tour_load.get(t.tour_id, 0) + t.n_parcels
        tour_vehicle[t.tour_id] = t.vehicle_id
    for tour_id, load in tour_load.items():
        assert load <= vehicle_capacity[tour_vehicle[tour_id]]


def test_all_stops_in_tour_share_depot(zones, depots, carriers, vehicles, skim, demand_config):
    demands = generate_parcel_demand(zones, depots, carriers, skim, demand_config)
    trips = schedule_parcel_deliveries(demands, depots, vehicles, skim)
    tour_depots: dict[int, set[int]] = {}
    for t in trips:
        tour_depots.setdefault(t.tour_id, set()).add(t.depot_id)
    assert all(len(ds) == 1 for ds in tour_depots.values())
