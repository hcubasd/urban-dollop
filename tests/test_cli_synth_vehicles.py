import pandas as pd
import pytest

from urban_dollop.cli.synth_vehicles import read_vehicles, vehicles_need_synthesis


def _row(vehicle, filled):
    if filled:
        return {
            "vehicle": vehicle,
            "vehicle_type": "vehicle_type_1",
            "bpr_alpha": 0.15,
            "bpr_beta": 4.0,
            "time_coefficient": -0.5,
            "distance_coefficient": -0.3,
            "pcu": 1.0,
        }
    return {
        "vehicle": vehicle,
        "vehicle_type": None,
        "bpr_alpha": None,
        "bpr_beta": None,
        "time_coefficient": None,
        "distance_coefficient": None,
        "pcu": None,
    }


def test_read_vehicles_none_if_absent(tmp_path):
    assert read_vehicles(str(tmp_path / "missing.csv")) is None


def test_read_vehicles_shape_only(tmp_path):
    path = tmp_path / "vehicles.csv"
    pd.DataFrame([_row("truck", False), _row("van", False)]).to_csv(path, index=False)
    vehicle_list, complete = read_vehicles(str(path))
    assert vehicle_list == ["truck", "van"]
    assert complete is False


def test_read_vehicles_complete(tmp_path):
    path = tmp_path / "vehicles.csv"
    pd.DataFrame([_row("truck", True)]).to_csv(path, index=False)
    vehicle_list, complete = read_vehicles(str(path))
    assert vehicle_list == ["truck"]
    assert complete is True


def test_read_vehicles_missing_column_rejected(tmp_path):
    path = tmp_path / "bad.csv"
    pd.DataFrame({"vehicle": ["truck"]}).to_csv(path, index=False)
    with pytest.raises(ValueError):
        read_vehicles(str(path))


def test_read_vehicles_duplicate_vehicles_rejected(tmp_path):
    path = tmp_path / "bad.csv"
    pd.DataFrame([_row("truck", False), _row("truck", False)]).to_csv(path, index=False)
    with pytest.raises(ValueError):
        read_vehicles(str(path))


def test_read_vehicles_one_column_filled_others_empty_rejected(tmp_path):
    path = tmp_path / "bad.csv"
    row = _row("truck", False)
    row["bpr_alpha"] = 0.15
    pd.DataFrame([row]).to_csv(path, index=False)
    with pytest.raises(ValueError):
        read_vehicles(str(path))


def test_vehicles_need_synthesis_true_when_absent():
    assert vehicles_need_synthesis(None) is True


def test_vehicles_need_synthesis_true_when_shape_only():
    assert vehicles_need_synthesis((["a"], False)) is True


def test_vehicles_need_synthesis_false_when_complete():
    assert vehicles_need_synthesis((["a"], True)) is False
