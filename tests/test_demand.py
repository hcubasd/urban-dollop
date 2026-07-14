import pytest

from urban_dollop import generate_logit_demand, generate_parcel_demand
from urban_dollop.models.carrier import Carrier
from urban_dollop.models.depot import Depot
from urban_dollop.models.logit_zone import LogitZone
from urban_dollop.parcel_demand.logit_config import LogitDemandConfig


def zone_total(zone, config):
    return int(
        round(
            zone.households * config.parcels_per_household / config.delivery_success_b2c
            + zone.employment
            * config.parcels_per_employee
            / config.delivery_success_b2b
        )
    )


def test_total_parcels_match_zone_formula(zones, depots, carriers, skim, demand_config):
    expected = sum(zone_total(z, demand_config) for z in zones)
    demands = generate_parcel_demand(zones, depots, carriers, skim, demand_config)
    assert sum(d.n_parcels for d in demands) == expected


def test_all_destination_zones_are_input_zones(
    zones, depots, carriers, skim, demand_config
):
    valid_ids = {z.zone_id for z in zones}
    demands = generate_parcel_demand(zones, depots, carriers, skim, demand_config)
    assert all(d.destination_zone_id in valid_ids for d in demands)


def test_all_origin_zones_are_depot_zones(zones, depots, carriers, skim, demand_config):
    valid_zone_ids = {d.zone_id for d in depots}
    demands = generate_parcel_demand(zones, depots, carriers, skim, demand_config)
    assert all(d.origin_zone_id in valid_zone_ids for d in demands)


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


def test_zero_share_carrier_without_depots_is_allowed(
    zones, depots, carriers, skim, demand_config
):
    ghost = Carrier(name="ghost", share=0.0)
    demands = generate_parcel_demand(
        zones, depots, carriers + [ghost], skim, demand_config
    )
    assert len(demands) > 0


def test_raises_for_nonzero_share_carrier_without_depots(
    zones, depots, carriers, skim, demand_config
):
    bad = [Carrier(name="alpha", share=0.6), Carrier(name="missing", share=0.4)]
    with pytest.raises(ValueError, match="non-zero market share but no depots"):
        generate_parcel_demand(zones, depots, bad, skim, demand_config)


def test_raises_for_depot_zone_not_in_skim(
    zones, depots, carriers, skim, demand_config
):
    bad_depots = depots + [Depot(depot_id=99, carrier="alpha", zone_id=9999)]
    with pytest.raises(ValueError, match="not present in the skim"):
        generate_parcel_demand(zones, bad_depots, carriers, skim, demand_config)


def test_raises_for_carrier_shares_not_summing_to_one(
    zones, depots, carriers, skim, demand_config
):
    bad = [Carrier(name="alpha", share=0.5), Carrier(name="beta", share=0.3)]
    with pytest.raises(ValueError, match="must sum to 1.0"):
        generate_parcel_demand(zones, depots, bad, skim, demand_config)


def test_calibration_target_scales_total(zones, depots, carriers, skim, demand_config):
    from urban_dollop.parcel_demand.config import ParcelDemandConfig

    config = demand_config.model_copy(update={"calibration_target": 100.0})
    demands = generate_parcel_demand(zones, depots, carriers, skim, config)
    total = sum(d.n_parcels for d in demands)
    assert abs(total - 100) <= len(zones)


def test_calibration_target_preserves_spatial_distribution(
    zones, depots, carriers, skim, demand_config
):
    uncalibrated = generate_parcel_demand(zones, depots, carriers, skim, demand_config)
    from urban_dollop.parcel_demand.config import ParcelDemandConfig

    config = demand_config.model_copy(update={"calibration_target": 200.0})
    calibrated = generate_parcel_demand(zones, depots, carriers, skim, config)
    uncal_zones = {d.destination_zone_id for d in uncalibrated}
    cal_zones = {d.destination_zone_id for d in calibrated}
    assert uncal_zones == cal_zones


def test_raises_for_non_positive_calibration_target(
    zones, depots, carriers, skim, demand_config
):
    from urban_dollop.parcel_demand.config import ParcelDemandConfig

    with pytest.raises(Exception, match="positive"):
        ParcelDemandConfig(
            parcels_per_household=0.1,
            parcels_per_employee=0.04,
            delivery_success_b2c=1.0,
            delivery_success_b2b=1.0,
            calibration_target=0.0,
        )


# ---------------------------------------------------------------------------
# Ordered logit formulation
# ---------------------------------------------------------------------------


def test_logit_returns_parcel_demands(
    logit_zones, depots, carriers, skim, logit_config
):
    demands = generate_logit_demand(logit_zones, depots, carriers, skim, logit_config)
    assert isinstance(demands, list)
    assert len(demands) > 0
    assert all(d.n_parcels > 0 for d in demands)


def test_logit_all_destination_zones_are_input_zones(
    logit_zones, depots, carriers, skim, logit_config
):
    valid_ids = {z.zone_id for z in logit_zones}
    demands = generate_logit_demand(logit_zones, depots, carriers, skim, logit_config)
    assert all(d.destination_zone_id in valid_ids for d in demands)


def test_logit_all_origin_zones_are_depot_zones(
    logit_zones, depots, carriers, skim, logit_config
):
    valid_zone_ids = {d.zone_id for d in depots}
    demands = generate_logit_demand(logit_zones, depots, carriers, skim, logit_config)
    assert all(d.origin_zone_id in valid_zone_ids for d in demands)


def test_logit_calibration_target_scales_total(
    logit_zones, depots, carriers, skim, logit_config
):
    config = logit_config.model_copy(update={"calibration_target": 100.0})
    demands = generate_logit_demand(logit_zones, depots, carriers, skim, config)
    total = sum(d.n_parcels for d in demands)
    assert abs(total - 100) <= len(logit_zones)


def test_logit_config_raises_for_wrong_mu_length():
    with pytest.raises(Exception, match="mu_thresholds"):
        LogitDemandConfig(
            beta_urbanization={1: 0.0},
            mu_thresholds=[1.0, 2.0],  # 2 thresholds requires 3 parcel levels
            parcel_levels=[0, 1, 2, 3, 4, 5, 10, 15, 20],
            reference_period_days=60.0,
        )


def test_logit_higher_urbanization_produces_more_demand(depots, carriers, skim):
    low_urb = [
        LogitZone(zone_id=i, population=100, urbanization_level=1)
        for i in range(1, 5)
    ]
    high_urb = [
        LogitZone(zone_id=i, population=100, urbanization_level=2)
        for i in range(1, 5)
    ]
    config = LogitDemandConfig(
        beta_urbanization={1: 0.0, 2: 2.0},
        mu_thresholds=[1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0],
        parcel_levels=[0, 1, 2, 3, 4, 5, 10, 15, 20],
        reference_period_days=60.0,
    )
    low_total = sum(
        d.n_parcels
        for d in generate_logit_demand(low_urb, depots, carriers, skim, config)
    )
    high_total = sum(
        d.n_parcels
        for d in generate_logit_demand(high_urb, depots, carriers, skim, config)
    )
    assert high_total > low_total


# ---------------------------------------------------------------------------
# Demographic stratification (age × income) tests
# ---------------------------------------------------------------------------

def _strata_config(depots, carriers, skim, logit_config):
    """Shared setup: two age cohorts × two income brackets, logit config with betas."""
    zones = [
        LogitZone(
            zone_id=i,
            population=400,
            urbanization_level=1,
            population_strata={1: {1: 100.0, 2: 100.0}, 2: {1: 100.0, 2: 100.0}},
        )
        for i in range(1, 5)
    ]
    config = LogitDemandConfig(
        beta_urbanization=logit_config.beta_urbanization,
        mu_thresholds=logit_config.mu_thresholds,
        parcel_levels=logit_config.parcel_levels,
        reference_period_days=logit_config.reference_period_days,
        beta_age={1: 0.0, 2: 0.5},
        beta_income={1: 0.0, 2: 1.0},
    )
    return zones, config


def test_stratified_returns_parcel_demands(depots, carriers, skim, logit_config):
    zones, config = _strata_config(depots, carriers, skim, logit_config)
    demands = generate_logit_demand(zones, depots, carriers, skim, config)
    assert len(demands) > 0


def test_stratified_higher_income_produces_more_demand(depots, carriers, skim, logit_config):
    base_config = LogitDemandConfig(
        beta_urbanization={1: 0.0},
        mu_thresholds=logit_config.mu_thresholds,
        parcel_levels=logit_config.parcel_levels,
        reference_period_days=logit_config.reference_period_days,
        beta_age={1: 0.0},
        beta_income={1: 0.0, 2: 2.0},
    )
    low_income_zones = [
        LogitZone(
            zone_id=i, population=100, urbanization_level=1,
            population_strata={1: {1: 100.0}},
        )
        for i in range(1, 5)
    ]
    high_income_zones = [
        LogitZone(
            zone_id=i, population=100, urbanization_level=1,
            population_strata={1: {2: 100.0}},
        )
        for i in range(1, 5)
    ]
    low_total = sum(
        d.n_parcels for d in generate_logit_demand(low_income_zones, depots, carriers, skim, base_config)
    )
    high_total = sum(
        d.n_parcels for d in generate_logit_demand(high_income_zones, depots, carriers, skim, base_config)
    )
    assert high_total > low_total


def test_stratified_strata_sum_equals_urbanization_only_when_betas_zero(
    depots, carriers, skim, logit_config
):
    config_urb = LogitDemandConfig(
        beta_urbanization={1: 0.3},
        mu_thresholds=logit_config.mu_thresholds,
        parcel_levels=logit_config.parcel_levels,
        reference_period_days=logit_config.reference_period_days,
    )
    config_strata = LogitDemandConfig(
        beta_urbanization={1: 0.3},
        mu_thresholds=logit_config.mu_thresholds,
        parcel_levels=logit_config.parcel_levels,
        reference_period_days=logit_config.reference_period_days,
        beta_age={1: 0.0},
        beta_income={1: 0.0},
    )
    zones_urb = [
        LogitZone(zone_id=i, population=200.0, urbanization_level=1)
        for i in range(1, 5)
    ]
    zones_strata = [
        LogitZone(
            zone_id=i, population=200.0, urbanization_level=1,
            population_strata={1: {1: 200.0}},
        )
        for i in range(1, 5)
    ]
    total_urb = sum(
        d.n_parcels for d in generate_logit_demand(zones_urb, depots, carriers, skim, config_urb)
    )
    total_strata = sum(
        d.n_parcels for d in generate_logit_demand(zones_strata, depots, carriers, skim, config_strata)
    )
    assert total_urb == total_strata


def test_stratified_raises_when_zone_missing_strata(depots, carriers, skim, logit_config):
    config = LogitDemandConfig(
        beta_urbanization={1: 0.0},
        mu_thresholds=logit_config.mu_thresholds,
        parcel_levels=logit_config.parcel_levels,
        reference_period_days=logit_config.reference_period_days,
        beta_age={1: 0.0},
        beta_income={1: 0.0},
    )
    zones = [LogitZone(zone_id=i, population=100, urbanization_level=1) for i in range(1, 5)]
    with pytest.raises(ValueError, match="population_strata"):
        generate_logit_demand(zones, depots, carriers, skim, config)


def test_logit_config_raises_when_only_one_demographic_beta_provided(logit_config):
    with pytest.raises(ValueError, match="beta_age and beta_income"):
        LogitDemandConfig(
            beta_urbanization={1: 0.0},
            mu_thresholds=logit_config.mu_thresholds,
            parcel_levels=logit_config.parcel_levels,
            reference_period_days=logit_config.reference_period_days,
            beta_age={1: 0.0},
        )
