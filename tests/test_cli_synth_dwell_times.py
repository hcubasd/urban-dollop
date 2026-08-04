import pandas as pd
import pytest

from urban_dollop.cli.synth_dwell_times import read_dwell_times, dwell_times_need_synthesis


def test_read_dwell_times_none_if_absent(tmp_path):
    assert read_dwell_times(str(tmp_path / "missing.csv")) is None


def test_read_dwell_times_shape_only(tmp_path):
    path = tmp_path / "dwell_times.csv"
    pd.DataFrame({"resource": ["grains", "parcels"], "dwell_time": [None, None], "load_pct": [None, None]}).to_csv(path, index=False)
    resources, complete = read_dwell_times(str(path))
    assert resources == ["grains", "parcels"]
    assert complete is False


def test_read_dwell_times_complete(tmp_path):
    path = tmp_path / "dwell_times.csv"
    pd.DataFrame({"resource": ["grains"], "dwell_time": [1.2], "load_pct": [0.4]}).to_csv(path, index=False)
    resources, complete = read_dwell_times(str(path))
    assert resources == ["grains"]
    assert complete is True


def test_read_dwell_times_missing_column_rejected(tmp_path):
    path = tmp_path / "bad.csv"
    pd.DataFrame({"resource": ["a"], "dwell_time": [1.0]}).to_csv(path, index=False)
    with pytest.raises(ValueError):
        read_dwell_times(str(path))


def test_read_dwell_times_duplicate_resources_rejected(tmp_path):
    path = tmp_path / "bad.csv"
    pd.DataFrame({"resource": ["a", "a"], "dwell_time": [None, None], "load_pct": [None, None]}).to_csv(path, index=False)
    with pytest.raises(ValueError):
        read_dwell_times(str(path))


def test_read_dwell_times_one_column_filled_other_empty_rejected(tmp_path):
    path = tmp_path / "bad.csv"
    pd.DataFrame({"resource": ["a"], "dwell_time": [1.0], "load_pct": [None]}).to_csv(path, index=False)
    with pytest.raises(ValueError):
        read_dwell_times(str(path))


def test_dwell_times_need_synthesis_true_when_absent():
    assert dwell_times_need_synthesis(None) is True


def test_dwell_times_need_synthesis_true_when_shape_only():
    assert dwell_times_need_synthesis((["a"], False)) is True


def test_dwell_times_need_synthesis_false_when_complete():
    assert dwell_times_need_synthesis((["a"], True)) is False
