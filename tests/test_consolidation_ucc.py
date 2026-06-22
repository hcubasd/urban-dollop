import pytest

from urban_dollop import consolidate_uccs
from urban_dollop.consolidation.ucc_config import UCCConfig
from urban_dollop.models.parcel_demand import ParcelDemand
from urban_dollop.models.ucc import UCC


def test_non_catchment_demands_pass_through(uccs, ucc_catchment_zones, skim_distance, ucc_config):
    # Non-catchment demand → dest=1 (not in catchment {3,4})
    # Catchment demand: origin=2→dest=4; nearest UCC for that pair is zone 2
    #   z1: dist(2→1)+dist(1→4)=10+15=25; z2: dist(2→2)+dist(2→4)=0+8=8 ← nearest
    # Leg A ends at zone 2, not zone 1, so no collision with non-catchment dest
    demands = [
        ParcelDemand(origin_zone_id=1, destination_zone_id=1, carrier="alpha", n_parcels=10),
        ParcelDemand(origin_zone_id=2, destination_zone_id=4, carrier="beta", n_parcels=6),
    ]
    result = consolidate_uccs(demands, uccs, ucc_catchment_zones, skim_distance, ucc_config)
    direct = [r for r in result if r.destination_zone_id == 1]
    assert len(direct) == 1
    assert direct[0].n_parcels == 10


def test_catchment_demand_produces_two_legs(ucc_catchment_zones, uccs, skim_distance, ucc_config):
    demands = [ParcelDemand(origin_zone_id=1, destination_zone_id=3, carrier="alpha", n_parcels=10)]
    result = consolidate_uccs(demands, uccs, ucc_catchment_zones, skim_distance, ucc_config)
    assert len(result) == 2


def test_leg_a_destination_is_ucc_zone(ucc_catchment_zones, uccs, skim_distance, ucc_config):
    demands = [ParcelDemand(origin_zone_id=1, destination_zone_id=3, carrier="alpha", n_parcels=10)]
    result = consolidate_uccs(demands, uccs, ucc_catchment_zones, skim_distance, ucc_config)
    ucc_zones = {u.zone_id for u in uccs}
    leg_a = next(r for r in result if r.origin_zone_id == 1)
    assert leg_a.destination_zone_id in ucc_zones


def test_leg_b_origin_is_ucc_zone(ucc_catchment_zones, uccs, skim_distance, ucc_config):
    demands = [ParcelDemand(origin_zone_id=1, destination_zone_id=3, carrier="alpha", n_parcels=10)]
    result = consolidate_uccs(demands, uccs, ucc_catchment_zones, skim_distance, ucc_config)
    ucc_zones = {u.zone_id for u in uccs}
    leg_b = next(r for r in result if r.destination_zone_id == 3)
    assert leg_b.origin_zone_id in ucc_zones


def test_leg_b_destination_is_original(ucc_catchment_zones, uccs, skim_distance, ucc_config):
    demands = [ParcelDemand(origin_zone_id=3, destination_zone_id=4, carrier="alpha", n_parcels=10)]
    result = consolidate_uccs(demands, uccs, ucc_catchment_zones, skim_distance, ucc_config)
    leg_b = next(r for r in result if r.destination_zone_id == 4)
    assert leg_b.destination_zone_id == 4
    assert leg_b.n_parcels == 10


def test_partial_probability_splits_parcels(ucc_catchment_zones, uccs, skim_distance):
    config = UCCConfig(probability=0.5)
    demands = [ParcelDemand(origin_zone_id=1, destination_zone_id=3, carrier="alpha", n_parcels=10)]
    result = consolidate_uccs(demands, uccs, ucc_catchment_zones, skim_distance, config)
    # 5 rerouted → leg A (5) + leg B (5); 5 direct → 3 records total
    assert len(result) == 3
    ucc_zones = {u.zone_id for u in uccs}
    direct = next(r for r in result if r.destination_zone_id == 3 and r.origin_zone_id == 1)
    assert direct.n_parcels == 5
    leg_b = next(r for r in result if r.destination_zone_id == 3 and r.origin_zone_id in ucc_zones)
    assert leg_b.n_parcels == 5


def test_nearest_ucc_minimises_total_distance(ucc_catchment_zones, skim_distance, ucc_config):
    # Origin=zone 3, destination=zone 4
    # UCC at zone 1: dist(3→1) + dist(1→4) = 20 + 15 = 35
    # UCC at zone 2: dist(3→2) + dist(2→4) = 12 + 8  = 20  ← nearest
    two_uccs = [UCC(ucc_id=1, zone_id=1), UCC(ucc_id=2, zone_id=2)]
    demands = [ParcelDemand(origin_zone_id=3, destination_zone_id=4, carrier="alpha", n_parcels=10)]
    result = consolidate_uccs(demands, two_uccs, ucc_catchment_zones, skim_distance, ucc_config)
    leg_b = next(r for r in result if r.destination_zone_id == 4)
    assert leg_b.origin_zone_id == 2


def test_uccs_are_carrier_agnostic(catchment_demands, uccs, ucc_catchment_zones, skim_distance, ucc_config):
    result = consolidate_uccs(catchment_demands, uccs, ucc_catchment_zones, skim_distance, ucc_config)
    ucc_zones = {u.zone_id for u in uccs}
    for r in result:
        if r.origin_zone_id in ucc_zones:
            assert r.carrier in {"alpha", "beta"}


def test_raises_for_no_uccs_with_catchment(ucc_catchment_zones, skim_distance, ucc_config):
    demands = [ParcelDemand(origin_zone_id=1, destination_zone_id=3, carrier="alpha", n_parcels=5)]
    with pytest.raises(ValueError, match="no UCCs are configured"):
        consolidate_uccs(demands, [], ucc_catchment_zones, skim_distance, ucc_config)


def test_raises_for_invalid_probability():
    with pytest.raises(Exception, match="probability"):
        UCCConfig(probability=0.0)


def test_empty_demands_returns_empty(uccs, ucc_catchment_zones, skim_distance, ucc_config):
    assert consolidate_uccs([], uccs, ucc_catchment_zones, skim_distance, ucc_config) == []
