import numpy as np
import pytest

from urban_dollop.freight_demand import FreightDemandConfig, generate_freight_demand
from urban_dollop.models.firm import Firm
from urban_dollop.models.freight_mnl_param import FreightMNLParam
from urban_dollop.models.freight_total import FreightTotal
from urban_dollop.models.freight_vehicle_params import FreightVehicleParams
from urban_dollop.models.make_use_coefficient import MakeUseCoefficient
from urban_dollop.models.shipment_size_class import ShipmentSizeClass
from urban_dollop.models.skim_distance import SkimDistance
from urban_dollop.models.skim_matrix import SkimMatrix
from urban_dollop.models.zone import Zone


# ── fixture helpers ───────────────────────────────────────────────────────────

def two_zone_skim_time() -> SkimMatrix:
    zones = [Zone(zone_id=1, x=0.0, y=0.0), Zone(zone_id=2, x=10.0, y=10.0)]
    data = np.array([0.0, 3600.0, 3600.0, 0.0], dtype=np.float32)
    return SkimMatrix(data=data, zones=zones)


def two_zone_skim_dist() -> SkimDistance:
    zones = [Zone(zone_id=1, x=0.0, y=0.0), Zone(zone_id=2, x=10.0, y=10.0)]
    data = np.array([0.0, 10000.0, 10000.0, 0.0], dtype=np.float32)
    return SkimDistance(data=data, zones=zones)


def basic_firms() -> list[Firm]:
    return [
        Firm(firm_id=1, zone_id=1, employment_sector=1, employment=50.0, x_coord=0.0, y_coord=0.0),
        Firm(firm_id=2, zone_id=2, employment_sector=1, employment=50.0, x_coord=10.0, y_coord=10.0),
    ]


def basic_totals(tonnes: float = 5.0) -> list[FreightTotal]:
    return [FreightTotal(logistic_segment=1, tonnes_day=tonnes)]


def basic_make_use() -> list[MakeUseCoefficient]:
    return [MakeUseCoefficient(logistic_segment=1, employment_sector=1, make_share=1.0, use_share=1.0)]


def basic_size_classes() -> list[ShipmentSizeClass]:
    return [ShipmentSizeClass(logistic_segment=1, size_class=1, weight_kg=500.0)]


def basic_vehicle_params() -> list[FreightVehicleParams]:
    return [FreightVehicleParams(vehicle_id=1, capacity_kg=1000.0, cost_per_hour=30.0, cost_per_km=0.40)]


def basic_mnl_params() -> list[FreightMNLParam]:
    return [
        FreightMNLParam(logistic_segment=-1, parameter="B_TransportCosts", value=-0.001),
        FreightMNLParam(logistic_segment=-1, parameter="B_InventoryCosts", value=-0.001),
    ]


def basic_config(seed: int = 0) -> FreightDemandConfig:
    return FreightDemandConfig(seed=seed)


def run(**kwargs):
    defaults = dict(
        firms=basic_firms(),
        freight_totals=basic_totals(),
        make_use=basic_make_use(),
        size_classes=basic_size_classes(),
        vehicle_params=basic_vehicle_params(),
        mnl_params=basic_mnl_params(),
        skim_time=two_zone_skim_time(),
        skim_distance=two_zone_skim_dist(),
        config=basic_config(),
    )
    defaults.update(kwargs)
    return generate_freight_demand(**defaults)


# ── output structure ──────────────────────────────────────────────────────────

def test_zero_budget_returns_empty():
    shipments = run(freight_totals=[FreightTotal(logistic_segment=1, tonnes_day=0.0)])
    assert shipments == []


def test_produces_at_least_one_shipment():
    shipments = run()
    assert len(shipments) > 0


def test_shipment_ids_sequential_from_one():
    shipments = run()
    assert [s.shipment_id for s in shipments] == list(range(1, len(shipments) + 1))


def test_origin_zone_is_a_skim_zone():
    skim = two_zone_skim_time()
    valid_zones = {z.zone_id for z in skim.zones}
    shipments = run()
    for s in shipments:
        assert s.origin_zone_id in valid_zones


def test_destination_zone_is_a_skim_zone():
    skim = two_zone_skim_time()
    valid_zones = {z.zone_id for z in skim.zones}
    shipments = run()
    for s in shipments:
        assert s.destination_zone_id in valid_zones


def test_vehicle_id_matches_vehicle_params():
    vp = basic_vehicle_params()
    valid_vt = {v.vehicle_id for v in vp}
    shipments = run()
    for s in shipments:
        assert s.vehicle_id in valid_vt


def test_weight_class_matches_size_classes():
    sc = basic_size_classes()
    valid_sc = {c.size_class for c in sc}
    shipments = run()
    for s in shipments:
        assert s.weight_class in valid_sc


# ── weight accounting ─────────────────────────────────────────────────────────

def test_total_weight_does_not_exceed_budget():
    budget_kg = 5.0 * 1000.0
    shipments = run()
    total = sum(s.weight_kg for s in shipments)
    assert total <= budget_kg + 1e-6


def test_total_weight_close_to_budget():
    tonnes = 10.0
    shipments = run(freight_totals=[FreightTotal(logistic_segment=1, tonnes_day=tonnes)])
    total_kg = sum(s.weight_kg for s in shipments)
    assert total_kg >= tonnes * 1000.0 * 0.9


def test_last_shipment_capped_at_remaining_weight():
    # Budget of 1250 kg with size class of 500 kg → 2 full + 1 partial of 250
    shipments = run(
        freight_totals=[FreightTotal(logistic_segment=1, tonnes_day=1.25)],
        size_classes=[ShipmentSizeClass(logistic_segment=1, size_class=1, weight_kg=500.0)],
        config=FreightDemandConfig(seed=0),
    )
    total = sum(s.weight_kg for s in shipments)
    assert total == pytest.approx(1250.0, abs=1e-6)


# ── multiple logistic segments ────────────────────────────────────────────────

def test_multiple_logistic_segments_both_produce_shipments():
    totals = [
        FreightTotal(logistic_segment=1, tonnes_day=2.0),
        FreightTotal(logistic_segment=2, tonnes_day=2.0),
    ]
    make_use = [
        MakeUseCoefficient(logistic_segment=1, employment_sector=1, make_share=1.0, use_share=1.0),
        MakeUseCoefficient(logistic_segment=2, employment_sector=1, make_share=1.0, use_share=1.0),
    ]
    size_classes = [
        ShipmentSizeClass(logistic_segment=1, size_class=1, weight_kg=500.0),
        ShipmentSizeClass(logistic_segment=2, size_class=1, weight_kg=500.0),
    ]
    shipments = run(freight_totals=totals, make_use=make_use, size_classes=size_classes)
    ls_set = {s.logistic_segment for s in shipments}
    assert ls_set == {1, 2}


# ── MNL alternatives ──────────────────────────────────────────────────────────

def test_multiple_vehicles_both_drawn_over_many_shipments():
    vehicles = [
        FreightVehicleParams(vehicle_id=1, capacity_kg=500.0, cost_per_hour=30.0, cost_per_km=0.30),
        FreightVehicleParams(vehicle_id=2, capacity_kg=5000.0, cost_per_hour=60.0, cost_per_km=0.60),
    ]
    mnl_params = [
        FreightMNLParam(logistic_segment=-1, parameter="B_TransportCosts", value=-0.001),
        FreightMNLParam(logistic_segment=-1, parameter="B_InventoryCosts", value=-0.001),
        FreightMNLParam(logistic_segment=-1, parameter="ASC_VT_1", value=0.0),
        FreightMNLParam(logistic_segment=-1, parameter="ASC_VT_2", value=0.0),
    ]
    shipments = run(
        freight_totals=[FreightTotal(logistic_segment=1, tonnes_day=50.0)],
        vehicle_params=vehicles,
        mnl_params=mnl_params,
    )
    vt_set = {s.vehicle_id for s in shipments}
    assert len(vt_set) == 2


def test_multiple_size_classes_both_drawn():
    sizes = [
        ShipmentSizeClass(logistic_segment=1, size_class=1, weight_kg=100.0),
        ShipmentSizeClass(logistic_segment=1, size_class=2, weight_kg=1000.0),
    ]
    mnl_params = [
        FreightMNLParam(logistic_segment=-1, parameter="B_TransportCosts", value=-0.001),
        FreightMNLParam(logistic_segment=-1, parameter="B_InventoryCosts", value=0.0),
        FreightMNLParam(logistic_segment=-1, parameter="ASC_SS_1", value=0.0),
        FreightMNLParam(logistic_segment=-1, parameter="ASC_SS_2", value=0.0),
    ]
    shipments = run(
        freight_totals=[FreightTotal(logistic_segment=1, tonnes_day=50.0)],
        size_classes=sizes,
        mnl_params=mnl_params,
    )
    sc_set = {s.weight_class for s in shipments}
    assert len(sc_set) == 2


# ── per-LS MNL params override global ────────────────────────────────────────

def test_ls_specific_param_overrides_global():
    # LS 1 gets a very strong ASC for VT 2; VT 2 should dominate
    vehicles = [
        FreightVehicleParams(vehicle_id=1, capacity_kg=500.0, cost_per_hour=30.0, cost_per_km=0.30),
        FreightVehicleParams(vehicle_id=2, capacity_kg=5000.0, cost_per_hour=60.0, cost_per_km=0.60),
    ]
    mnl_params = [
        FreightMNLParam(logistic_segment=-1, parameter="B_TransportCosts", value=0.0),
        FreightMNLParam(logistic_segment=-1, parameter="B_InventoryCosts", value=0.0),
        FreightMNLParam(logistic_segment=-1, parameter="ASC_VT_1", value=0.0),
        FreightMNLParam(logistic_segment=-1, parameter="ASC_VT_2", value=0.0),
        FreightMNLParam(logistic_segment=1, parameter="ASC_VT_2", value=100.0),
    ]
    shipments = run(
        freight_totals=[FreightTotal(logistic_segment=1, tonnes_day=50.0)],
        vehicle_params=vehicles,
        mnl_params=mnl_params,
    )
    assert all(s.vehicle_id == 2 for s in shipments)


# ── reproducibility ───────────────────────────────────────────────────────────

def test_seed_makes_synthesis_reproducible():
    s1 = run(config=FreightDemandConfig(seed=42))
    s2 = run(config=FreightDemandConfig(seed=42))
    assert len(s1) == len(s2)
    assert s1[0].origin_zone_id == s2[0].origin_zone_id
    assert s1[0].destination_zone_id == s2[0].destination_zone_id


def test_different_seeds_give_different_results():
    s1 = run(
        freight_totals=[FreightTotal(logistic_segment=1, tonnes_day=20.0)],
        config=FreightDemandConfig(seed=1),
    )
    s2 = run(
        freight_totals=[FreightTotal(logistic_segment=1, tonnes_day=20.0)],
        config=FreightDemandConfig(seed=2),
    )
    origins1 = [s.origin_zone_id for s in s1]
    origins2 = [s.origin_zone_id for s in s2]
    assert origins1 != origins2


# ── validation errors ─────────────────────────────────────────────────────────

def test_missing_ls_in_make_use_raises():
    with pytest.raises(ValueError, match="make_use_coefficients"):
        run(
            freight_totals=[FreightTotal(logistic_segment=99, tonnes_day=1.0)],
            make_use=basic_make_use(),
            size_classes=[ShipmentSizeClass(logistic_segment=99, size_class=1, weight_kg=100.0)],
        )


def test_missing_size_class_for_ls_raises():
    with pytest.raises(ValueError, match="size"):
        run(
            freight_totals=[FreightTotal(logistic_segment=99, tonnes_day=1.0)],
            make_use=[MakeUseCoefficient(logistic_segment=99, employment_sector=1, make_share=1.0, use_share=1.0)],
            size_classes=basic_size_classes(),
        )


def test_empty_vehicle_params_raises():
    with pytest.raises(ValueError, match="vehicle_params"):
        run(vehicle_params=[])
