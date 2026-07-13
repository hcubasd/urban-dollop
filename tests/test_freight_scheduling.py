import math

import pytest

from urban_dollop.freight_scheduling import FreightSchedulingConfig, schedule_freight
from urban_dollop.models.freight_vehicle_params import FreightVehicleParams
from urban_dollop.models.shipment import Shipment


def vp(vehicle_id=1, capacity_kg=1000.0):
    return FreightVehicleParams(vehicle_id=vehicle_id, capacity_kg=capacity_kg,
                                cost_per_hour=30.0, cost_per_km=0.40)


def ship(shipment_id=1, orig=1, dest=2, ls=1, veh=1, weight=500.0, cls=1):
    return Shipment(shipment_id=shipment_id, origin_zone_id=orig,
                    destination_zone_id=dest, logistic_segment=ls,
                    vehicle_id=veh, weight_kg=weight, weight_class=cls)


def run(shipments, vehicle_params, config=None):
    return schedule_freight(shipments, vehicle_params, config)


# ── basic output ──────────────────────────────────────────────────────────────

def test_empty_shipments_returns_empty():
    assert run([], [vp()]) == []


def test_trip_ids_sequential_from_one():
    trips = run([ship(1), ship(2)], [vp()])
    assert [t.trip_id for t in trips] == list(range(1, len(trips) + 1))


def test_origin_destination_carried_through():
    trips = run([ship(orig=3, dest=7)], [vp()])
    assert trips[0].origin_zone_id == 3
    assert trips[0].destination_zone_id == 7


def test_vehicle_id_carried_through():
    trips = run([ship(veh=2)], [vp(vehicle_id=2)])
    assert trips[0].vehicle_id == 2


# ── load consolidation ────────────────────────────────────────────────────────

def test_single_shipment_within_capacity_gives_one_trip():
    trips = run([ship(weight=500.0)], [vp(capacity_kg=1000.0)])
    assert len(trips) == 1


def test_single_shipment_exactly_at_capacity_gives_one_trip():
    trips = run([ship(weight=1000.0)], [vp(capacity_kg=1000.0)])
    assert len(trips) == 1


def test_two_shipments_within_capacity_consolidated_into_one_trip():
    shipments = [ship(1, weight=400.0), ship(2, weight=400.0)]
    trips = run(shipments, [vp(capacity_kg=1000.0)])
    assert len(trips) == 1


def test_shipments_exceeding_capacity_produce_multiple_trips():
    # 2500 kg with 1000 kg capacity → 3 trips
    shipments = [ship(i+1, weight=500.0) for i in range(5)]
    trips = run(shipments, [vp(capacity_kg=1000.0)])
    assert len(trips) == 3


def test_trip_count_is_ceiling_of_weight_over_capacity():
    total = 2500.0
    capacity = 1000.0
    shipments = [ship(1, weight=total)]
    trips = run(shipments, [vp(capacity_kg=capacity)])
    assert len(trips) == math.ceil(total / capacity)


# ── grouping ──────────────────────────────────────────────────────────────────

def test_different_od_pairs_produce_separate_trip_groups():
    shipments = [
        ship(1, orig=1, dest=2, weight=100.0),
        ship(2, orig=3, dest=4, weight=100.0),
    ]
    trips = run(shipments, [vp(capacity_kg=1000.0)])
    od_pairs = {(t.origin_zone_id, t.destination_zone_id) for t in trips}
    assert od_pairs == {(1, 2), (3, 4)}


def test_different_vehicle_types_produce_separate_trip_groups():
    shipments = [
        ship(1, veh=1, weight=500.0),
        ship(2, veh=2, weight=500.0),
    ]
    vehicles = [vp(vehicle_id=1, capacity_kg=1000.0), vp(vehicle_id=2, capacity_kg=1000.0)]
    trips = run(shipments, vehicles)
    vt_set = {t.vehicle_id for t in trips}
    assert vt_set == {1, 2}


def test_same_od_different_vehicles_not_consolidated():
    # Same OD but different vehicle_id → two separate groups
    shipments = [ship(1, veh=1, weight=100.0), ship(2, veh=2, weight=100.0)]
    vehicles = [vp(vehicle_id=1, capacity_kg=1000.0), vp(vehicle_id=2, capacity_kg=1000.0)]
    trips = run(shipments, vehicles)
    assert len(trips) == 2


# ── validation ────────────────────────────────────────────────────────────────

def test_unknown_vehicle_id_raises():
    with pytest.raises(ValueError, match="vehicle_id"):
        run([ship(veh=99)], [vp(vehicle_id=1)])


def test_config_is_optional():
    trips = run([ship()], [vp()], config=None)
    assert len(trips) == 1


def test_explicit_config_accepted():
    trips = run([ship()], [vp()], config=FreightSchedulingConfig())
    assert len(trips) == 1
