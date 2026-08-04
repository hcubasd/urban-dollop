import pandas as pd
import pytest

from urban_dollop.cli.synth_time_intervals import read_time_intervals, time_intervals_need_synthesis


def test_read_time_intervals_none_if_absent(tmp_path):
    assert read_time_intervals(str(tmp_path / "missing.csv")) is None


def test_read_time_intervals_shape_only(tmp_path):
    path = tmp_path / "time_intervals.csv"
    pd.DataFrame({"time_interval": ["AM_peak", "midday"], "duration": [None, None]}).to_csv(path, index=False)
    labels, complete = read_time_intervals(str(path))
    assert labels == ["AM_peak", "midday"]
    assert complete is False


def test_read_time_intervals_complete(tmp_path):
    path = tmp_path / "time_intervals.csv"
    pd.DataFrame({"time_interval": ["AM_peak", "midday"], "duration": [1.5, 3.0]}).to_csv(path, index=False)
    labels, complete = read_time_intervals(str(path))
    assert labels == ["AM_peak", "midday"]
    assert complete is True


def test_read_time_intervals_missing_column_rejected(tmp_path):
    path = tmp_path / "bad.csv"
    pd.DataFrame({"duration": [1.0]}).to_csv(path, index=False)
    with pytest.raises(ValueError):
        read_time_intervals(str(path))


def test_read_time_intervals_duplicate_labels_rejected(tmp_path):
    path = tmp_path / "bad.csv"
    pd.DataFrame({"time_interval": ["a", "a"], "duration": [None, None]}).to_csv(path, index=False)
    with pytest.raises(ValueError):
        read_time_intervals(str(path))


def test_read_time_intervals_mixed_duration_rejected(tmp_path):
    path = tmp_path / "bad.csv"
    pd.DataFrame({"time_interval": ["a", "b"], "duration": [1.0, None]}).to_csv(path, index=False)
    with pytest.raises(ValueError):
        read_time_intervals(str(path))


def test_time_intervals_need_synthesis_true_when_absent():
    assert time_intervals_need_synthesis(None) is True


def test_time_intervals_need_synthesis_true_when_shape_only():
    assert time_intervals_need_synthesis((["a"], False)) is True


def test_time_intervals_need_synthesis_false_when_complete():
    assert time_intervals_need_synthesis((["a"], True)) is False
