import pandas as pd
import pytest

from urban_dollop.cli.synth_vehicle_capacities import read_vehicle_capacities, vehicle_capacities_need_synthesis


def test_read_vehicle_capacities_none_if_absent(tmp_path):
    assert read_vehicle_capacities(str(tmp_path / "missing.csv")) is None


def test_read_vehicle_capacities_shape_only(tmp_path):
    path = tmp_path / "vehicle_capacities.csv"
    pd.DataFrame({
        "vehicle": ["truck", "van"],
        "resource": ["grains", "parcels"],
        "capacity": [None, None],
    }).to_csv(path, index=False)
    pairs, complete = read_vehicle_capacities(str(path))
    assert pairs == [
        {"vehicle": "truck", "resource": "grains"},
        {"vehicle": "van", "resource": "parcels"},
    ]
    assert complete is False


def test_read_vehicle_capacities_complete(tmp_path):
    path = tmp_path / "vehicle_capacities.csv"
    pd.DataFrame({"vehicle": ["truck"], "resource": ["grains"], "capacity": [12.0]}).to_csv(path, index=False)
    pairs, complete = read_vehicle_capacities(str(path))
    assert complete is True


def test_read_vehicle_capacities_missing_column_rejected(tmp_path):
    path = tmp_path / "bad.csv"
    pd.DataFrame({"vehicle": ["truck"], "resource": ["grains"]}).to_csv(path, index=False)
    with pytest.raises(ValueError):
        read_vehicle_capacities(str(path))


def test_read_vehicle_capacities_duplicate_pairs_rejected(tmp_path):
    path = tmp_path / "bad.csv"
    pd.DataFrame({
        "vehicle": ["truck", "truck"],
        "resource": ["grains", "grains"],
        "capacity": [None, None],
    }).to_csv(path, index=False)
    with pytest.raises(ValueError):
        read_vehicle_capacities(str(path))


def test_read_vehicle_capacities_mixed_capacity_rejected(tmp_path):
    path = tmp_path / "bad.csv"
    pd.DataFrame({
        "vehicle": ["truck", "van"],
        "resource": ["grains", "parcels"],
        "capacity": [12.0, None],
    }).to_csv(path, index=False)
    with pytest.raises(ValueError):
        read_vehicle_capacities(str(path))


def test_read_vehicle_capacities_fractional_capacity_rejected(tmp_path):
    path = tmp_path / "bad.csv"
    pd.DataFrame({"vehicle": ["truck"], "resource": ["grains"], "capacity": [12.5]}).to_csv(path, index=False)
    with pytest.raises(ValueError):
        read_vehicle_capacities(str(path))


def test_vehicle_capacities_need_synthesis_true_when_absent():
    assert vehicle_capacities_need_synthesis(None) is True


def test_vehicle_capacities_need_synthesis_true_when_shape_only():
    assert vehicle_capacities_need_synthesis(([{"vehicle": "a", "resource": "b"}], False)) is True


def test_vehicle_capacities_need_synthesis_false_when_complete():
    assert vehicle_capacities_need_synthesis(([{"vehicle": "a", "resource": "b"}], True)) is False
