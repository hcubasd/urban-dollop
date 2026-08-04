from urban_dollop.synth.copert_v_coefficients import (
    GRADIENT_BINS,
    PAYLOAD_BINS,
    copert_v_coefficients,
)


def test_zero_sigma_is_a_single_vehicle_type_single_pollutant():
    rows = copert_v_coefficients(sigma=0.0)
    vehicle_types = {r["vehicle_type"] for r in rows}
    pollutants = {r["pollutant"] for r in rows}
    assert vehicle_types == {"vehicle_type_1"}
    assert pollutants == {"pollutant_1"}


def test_full_cross_product_including_fixed_bins():
    rows = copert_v_coefficients(sigma=2.0)
    vehicle_types = {r["vehicle_type"] for r in rows}
    pollutants = {r["pollutant"] for r in rows}
    assert len(rows) == len(vehicle_types) * len(pollutants) * len(GRADIENT_BINS) * len(PAYLOAD_BINS)
    seen = {(r["vehicle_type"], r["pollutant"], r["gradient_bin"], r["payload_bin"]) for r in rows}
    assert seen == {
        (vt, p, g, pl)
        for vt in vehicle_types
        for p in pollutants
        for g in GRADIENT_BINS
        for pl in PAYLOAD_BINS
    }


def test_coefficients_can_be_any_sign():
    rows = copert_v_coefficients(sigma=2.0)
    for column in ("alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta"):
        assert all(isinstance(r[column], float) for r in rows)


def test_reduction_factor_is_bounded_zero_to_one():
    rows = copert_v_coefficients(sigma=2.0)
    assert all(0.0 <= r["rf"] <= 1.0 for r in rows)


def test_given_rows_used_as_is_and_ignore_sigma_for_shape():
    rows = [
        {"vehicle_type": "hdv", "pollutant": "nox", "gradient_bin": -4, "payload_bin": 50},
        {"vehicle_type": "ldv", "pollutant": "co2", "gradient_bin": 0, "payload_bin": 0},
    ]
    result = copert_v_coefficients(rows=rows, sigma=5.0)
    assert {(r["vehicle_type"], r["pollutant"], r["gradient_bin"], r["payload_bin"]) for r in result} == {
        ("hdv", "nox", -4, 50),
        ("ldv", "co2", 0, 0),
    }


def test_given_rows_need_not_cover_the_full_bin_grid():
    rows = [{"vehicle_type": "hdv", "pollutant": "nox", "gradient_bin": -4, "payload_bin": 50}]
    result = copert_v_coefficients(rows=rows, sigma=1.0)
    assert len(result) == 1
