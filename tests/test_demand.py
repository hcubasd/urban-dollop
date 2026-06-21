import pytest

from urban_dollop import generate_parcel_demand
from urban_dollop.models.carrier import Carrier
from urban_dollop.models.depot import Depot


def zone_total(zone, config):
    return int(round(
        zone.households * config.parcels_per_household / config.delivery_success_b2c
        + zone.employment * config.parcels_per_employee / config.delivery_success_b2b
    ))


def test_total_parcels_match_zone_formula(zones, depots, carriers, skim, demand_config):
    expected = sum(zone_total(z, demand_config) for z in zones)
    demands = generate_parcel_demand(zones, depots, carriers, skim, demand_config)
    assert sum(d.n_parcels for d in demands) == expected


def test_all_destination_zones_are_input_zones(zones, depots, carriers, skim, demand_config):
    valid_ids = {z.zone_id for z in zones}
    demands = generate_parcel_demand(zones, depots, carriers, skim, demand_config)
    assert all(d.destination_zone_id in valid_ids for d in demands)


def test_all_depot_ids_are_input_depots(zones, depots, carriers, skim, demand_config):
    valid_ids = {d.depot_id for d in depots}
    demands = generate_parcel_demand(zones, depots, carriers, skim, demand_config)
    assert all(d.depot_id in valid_ids for d in demands)


def test_no_zero_parcel_rows(zones, depots, carriers, skim, demand_config):
    demands = generate_parcel_demand(zones, depots, carriers, skim, demand_config)
    assert all(d.n_parcels > 0 for d in demands)


def test_zones_with_zero_demand_produce_no_rows(zones, depots, carriers, skim):
    from urban_dollop.parcel_demand.config import ParcelDemandConfig
    config = ParcelDemandConfig(
        parcels_per_household=0.0,
        parcels_per_employee=0.0,
        delivery_success_b2c=1.0,
        delivery_success_b2b=1.0,
    )
    demands = generate_parcel_demand(zones, depots, carriers, skim, config)
    assert demands == []


def test_zero_share_carrier_without_depots_is_allowed(zones, depots, carriers, skim, demand_config):
    ghost = Carrier(name="ghost", share=0.0)
    demands = generate_parcel_demand(zones, depots, carriers + [ghost], skim, demand_config)
    assert len(demands) > 0


def test_raises_for_nonzero_share_carrier_without_depots(zones, depots, carriers, skim, demand_config):
    bad = [Carrier(name="alpha", share=0.6), Carrier(name="missing", share=0.4)]
    with pytest.raises(ValueError, match="non-zero market share but no depots"):
        generate_parcel_demand(zones, depots, bad, skim, demand_config)


def test_raises_for_depot_zone_not_in_skim(zones, depots, carriers, skim, demand_config):
    bad_depots = depots + [Depot(depot_id=99, carrier="alpha", zone_id=9999)]
    with pytest.raises(ValueError, match="not present in the skim"):
        generate_parcel_demand(zones, bad_depots, carriers, skim, demand_config)


def test_raises_for_carrier_shares_not_summing_to_one(zones, depots, carriers, skim, demand_config):
    bad = [Carrier(name="alpha", share=0.5), Carrier(name="beta", share=0.3)]
    with pytest.raises(ValueError, match="must sum to 1.0"):
        generate_parcel_demand(zones, depots, bad, skim, demand_config)
