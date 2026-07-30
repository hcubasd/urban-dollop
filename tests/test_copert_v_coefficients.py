import pytest

from urban_dollop.synth.copert_v_coefficients import (
    copert_v_coefficients,
    GRADIENT_BINS,
    PAYLOAD_BINS,
)


@pytest.fixture(scope="module")
def rows():
    return copert_v_coefficients()


def test_returns_list_of_dicts(rows):
    assert isinstance(rows, list)
    assert all(isinstance(r, dict) for r in rows)


def test_has_required_columns(rows):
    for row in rows:
        for col in ("vehicle_type", "pollutant", "gradient_bin", "payload_bin",
                    "alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta", "rf"):
            assert col in row


def test_pollutants_are_synthetic_labels(rows):
    for row in rows:
        assert row["pollutant"].startswith("pollutant_")


def test_gradient_bins_are_standard(rows):
    for row in rows:
        assert row["gradient_bin"] in GRADIENT_BINS


def test_payload_bins_are_standard(rows):
    for row in rows:
        assert row["payload_bin"] in PAYLOAD_BINS


def test_rf_in_unit_interval(rows):
    for row in rows:
        assert 0.0 <= row["rf"] < 1.0


def test_coefficients_are_floats(rows):
    for row in rows:
        for col in ("alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta"):
            assert isinstance(row[col], float)


def test_full_cross_product(rows):
    vehicle_types = sorted(set(r["vehicle_type"] for r in rows))
    pollutants = sorted(set(r["pollutant"] for r in rows))
    expected = len(vehicle_types) * len(pollutants) * len(GRADIENT_BINS) * len(PAYLOAD_BINS)
    assert len(rows) == expected


def test_no_duplicate_rows(rows):
    keys = [(r["vehicle_type"], r["pollutant"], r["gradient_bin"], r["payload_bin"]) for r in rows]
    assert len(keys) == len(set(keys))
