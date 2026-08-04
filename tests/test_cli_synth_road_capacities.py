import pandas as pd
import pytest

from urban_dollop.cli.synth_road_capacities import read_road_capacities, road_capacities_need_synthesis


def test_read_road_capacities_none_if_absent(tmp_path):
    assert read_road_capacities(str(tmp_path / "missing.csv")) is None


def test_read_road_capacities_shape_only(tmp_path):
    path = tmp_path / "road_capacities.csv"
    pd.DataFrame({"road_type": ["highway", "residential"], "capacity": [None, None]}).to_csv(path, index=False)
    road_types, complete = read_road_capacities(str(path))
    assert road_types == ["highway", "residential"]
    assert complete is False


def test_read_road_capacities_complete(tmp_path):
    path = tmp_path / "road_capacities.csv"
    pd.DataFrame({"road_type": ["highway"], "capacity": [1800.0]}).to_csv(path, index=False)
    road_types, complete = read_road_capacities(str(path))
    assert road_types == ["highway"]
    assert complete is True


def test_read_road_capacities_missing_column_rejected(tmp_path):
    path = tmp_path / "bad.csv"
    pd.DataFrame({"capacity": [1.0]}).to_csv(path, index=False)
    with pytest.raises(ValueError):
        read_road_capacities(str(path))


def test_read_road_capacities_duplicate_road_types_rejected(tmp_path):
    path = tmp_path / "bad.csv"
    pd.DataFrame({"road_type": ["a", "a"], "capacity": [None, None]}).to_csv(path, index=False)
    with pytest.raises(ValueError):
        read_road_capacities(str(path))


def test_read_road_capacities_mixed_capacity_rejected(tmp_path):
    path = tmp_path / "bad.csv"
    pd.DataFrame({"road_type": ["a", "b"], "capacity": [1.0, None]}).to_csv(path, index=False)
    with pytest.raises(ValueError):
        read_road_capacities(str(path))


def test_road_capacities_need_synthesis_true_when_absent():
    assert road_capacities_need_synthesis(None) is True


def test_road_capacities_need_synthesis_true_when_shape_only():
    assert road_capacities_need_synthesis((["a"], False)) is True


def test_road_capacities_need_synthesis_false_when_complete():
    assert road_capacities_need_synthesis((["a"], True)) is False
