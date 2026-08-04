import pandas as pd
import pytest

from urban_dollop.cli.synth_copert_v_coefficients import (
    read_copert_v_coefficients,
    copert_v_coefficients_need_synthesis,
)


def _row(vehicle_type, filled):
    if filled:
        return {
            "vehicle_type": vehicle_type,
            "pollutant": "nox",
            "gradient_bin": 0,
            "payload_bin": 50,
            "alpha": 0.1,
            "beta": 0.2,
            "gamma": 0.3,
            "delta": 0.4,
            "epsilon": 0.5,
            "zeta": 0.6,
            "eta": 0.7,
            "rf": 0.8,
        }
    return {
        "vehicle_type": vehicle_type,
        "pollutant": "nox",
        "gradient_bin": 0,
        "payload_bin": 50,
        "alpha": None,
        "beta": None,
        "gamma": None,
        "delta": None,
        "epsilon": None,
        "zeta": None,
        "eta": None,
        "rf": None,
    }


def test_read_copert_v_coefficients_none_if_absent(tmp_path):
    assert read_copert_v_coefficients(str(tmp_path / "missing.csv")) is None


def test_read_copert_v_coefficients_shape_only(tmp_path):
    path = tmp_path / "copert_v_coefficients.csv"
    pd.DataFrame([_row("hdv", False), _row("ldv", False)]).to_csv(path, index=False)
    rows, complete = read_copert_v_coefficients(str(path))
    assert rows == [
        {"vehicle_type": "hdv", "pollutant": "nox", "gradient_bin": 0, "payload_bin": 50},
        {"vehicle_type": "ldv", "pollutant": "nox", "gradient_bin": 0, "payload_bin": 50},
    ]
    assert complete is False


def test_read_copert_v_coefficients_complete(tmp_path):
    path = tmp_path / "copert_v_coefficients.csv"
    pd.DataFrame([_row("hdv", True)]).to_csv(path, index=False)
    rows, complete = read_copert_v_coefficients(str(path))
    assert complete is True


def test_read_copert_v_coefficients_missing_column_rejected(tmp_path):
    path = tmp_path / "bad.csv"
    pd.DataFrame({"vehicle_type": ["hdv"]}).to_csv(path, index=False)
    with pytest.raises(ValueError):
        read_copert_v_coefficients(str(path))


def test_read_copert_v_coefficients_duplicate_keys_rejected(tmp_path):
    path = tmp_path / "bad.csv"
    pd.DataFrame([_row("hdv", False), _row("hdv", False)]).to_csv(path, index=False)
    with pytest.raises(ValueError):
        read_copert_v_coefficients(str(path))


def test_read_copert_v_coefficients_one_column_filled_others_empty_rejected(tmp_path):
    path = tmp_path / "bad.csv"
    row = _row("hdv", False)
    row["alpha"] = 0.1
    pd.DataFrame([row]).to_csv(path, index=False)
    with pytest.raises(ValueError):
        read_copert_v_coefficients(str(path))


def test_copert_v_coefficients_need_synthesis_true_when_absent():
    assert copert_v_coefficients_need_synthesis(None) is True


def test_copert_v_coefficients_need_synthesis_true_when_shape_only():
    assert copert_v_coefficients_need_synthesis(([{"vehicle_type": "hdv"}], False)) is True


def test_copert_v_coefficients_need_synthesis_false_when_complete():
    assert copert_v_coefficients_need_synthesis(([{"vehicle_type": "hdv"}], True)) is False
