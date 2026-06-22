import pytest

from urban_dollop import consolidate_microhubs
from urban_dollop.models.microhub import Microhub
from urban_dollop.models.parcel_demand import ParcelDemand
from urban_dollop.models.zero_emission_zone import ZeroEmissionZone


def test_non_zez_demands_pass_through(mixed_demands, microhubs, zez_zones, skim_distance):
    result = consolidate_microhubs(mixed_demands, microhubs, zez_zones, skim_distance)
    direct = [r for r in result if r.destination_zone_id == 3]
    assert len(direct) == 1
    assert direct[0].n_parcels == 10
    assert direct[0].origin_zone_id == 1
    assert direct[0].carrier == "alpha"


def test_zez_demand_produces_two_legs(zez_zones, microhubs, skim_distance):
    demands = [ParcelDemand(origin_zone_id=1, destination_zone_id=4, carrier="alpha", n_parcels=5)]
    result = consolidate_microhubs(demands, microhubs, zez_zones, skim_distance)
    assert len(result) == 2


def test_leg_a_destination_is_microhub_zone(zez_zones, microhubs, skim_distance):
    demands = [ParcelDemand(origin_zone_id=1, destination_zone_id=4, carrier="alpha", n_parcels=5)]
    result = consolidate_microhubs(demands, microhubs, zez_zones, skim_distance)
    mh_zones = {mh.zone_id for mh in microhubs if mh.carrier == "alpha"}
    leg_a = next(r for r in result if r.origin_zone_id == 1)
    assert leg_a.destination_zone_id in mh_zones


def test_leg_b_origin_is_microhub_zone(zez_zones, microhubs, skim_distance):
    demands = [ParcelDemand(origin_zone_id=1, destination_zone_id=4, carrier="alpha", n_parcels=5)]
    result = consolidate_microhubs(demands, microhubs, zez_zones, skim_distance)
    mh_zones = {mh.zone_id for mh in microhubs if mh.carrier == "alpha"}
    leg_b = next(r for r in result if r.destination_zone_id == 4)
    assert leg_b.origin_zone_id in mh_zones


def test_leg_b_destination_is_original(zez_zones, microhubs, skim_distance):
    # Origin zone 2 is not the alpha hub zone (zone 1), so the two legs are distinct
    demands = [ParcelDemand(origin_zone_id=2, destination_zone_id=4, carrier="alpha", n_parcels=5)]
    result = consolidate_microhubs(demands, microhubs, zez_zones, skim_distance)
    leg_b = next(r for r in result if r.origin_zone_id == 1)  # alpha hub at zone 1
    assert leg_b.destination_zone_id == 4


def test_parcel_count_preserved(mixed_demands, microhubs, zez_zones, skim_distance):
    result = consolidate_microhubs(mixed_demands, microhubs, zez_zones, skim_distance)
    # Each ZEZ-destined parcel appears in both leg A and leg B, so total
    # increases by the ZEZ parcel count. Direct parcels appear once.
    zez_parcels = sum(d.n_parcels for d in mixed_demands if d.destination_zone_id == 4)
    direct_parcels = sum(d.n_parcels for d in mixed_demands if d.destination_zone_id != 4)
    assert sum(r.n_parcels for r in result) == direct_parcels + 2 * zez_parcels


def test_nearest_microhub_selected(zez_zones, skim_distance):
    # Two alpha hubs: zone 1 (distance to zone 4 = 15) and zone 3 (distance = 18)
    # Zone 1 is closer, so leg B should originate from zone 1
    two_hubs = [
        Microhub(microhub_id=1, zone_id=1, carrier="alpha"),
        Microhub(microhub_id=2, zone_id=3, carrier="alpha"),
    ]
    demands = [ParcelDemand(origin_zone_id=2, destination_zone_id=4, carrier="alpha", n_parcels=10)]
    result = consolidate_microhubs(demands, two_hubs, zez_zones, skim_distance)
    leg_b = next(r for r in result if r.destination_zone_id == 4)
    assert leg_b.origin_zone_id == 1


def test_carrier_specific_hub_assignment(mixed_demands, microhubs, zez_zones, skim_distance):
    result = consolidate_microhubs(mixed_demands, microhubs, zez_zones, skim_distance)
    alpha_hub_zones = {mh.zone_id for mh in microhubs if mh.carrier == "alpha"}
    beta_hub_zones = {mh.zone_id for mh in microhubs if mh.carrier == "beta"}
    for r in result:
        if r.destination_zone_id == 4 and r.carrier == "alpha":
            assert r.origin_zone_id in alpha_hub_zones
        if r.destination_zone_id == 4 and r.carrier == "beta":
            assert r.origin_zone_id in beta_hub_zones


def test_raises_for_carrier_without_microhub(zez_zones, skim_distance):
    demands = [ParcelDemand(origin_zone_id=1, destination_zone_id=4, carrier="gamma", n_parcels=5)]
    microhubs = [Microhub(microhub_id=1, zone_id=1, carrier="alpha")]
    with pytest.raises(ValueError, match="no microhubs"):
        consolidate_microhubs(demands, microhubs, zez_zones, skim_distance)


def test_empty_demands_returns_empty(microhubs, zez_zones, skim_distance):
    assert consolidate_microhubs([], microhubs, zez_zones, skim_distance) == []
