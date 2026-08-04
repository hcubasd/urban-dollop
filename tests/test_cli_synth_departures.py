import pandas as pd
import pytest

from urban_dollop.cli.synth_departures import read_departures, departures_need_synthesis


def test_read_departures_none_if_absent(tmp_path):
    assert read_departures(str(tmp_path / "missing.csv")) is None


def test_read_departures_shape_only(tmp_path):
    path = tmp_path / "departures.csv"
    pd.DataFrame({
        "resource": ["grains", "grains", "parcels"],
        "time_interval": ["AM_peak", "PM_peak", "midday"],
        "probability": [None, None, None],
    }).to_csv(path, index=False)
    pairs, complete = read_departures(str(path))
    assert pairs == [
        {"resource": "grains", "time_interval": "AM_peak"},
        {"resource": "grains", "time_interval": "PM_peak"},
        {"resource": "parcels", "time_interval": "midday"},
    ]
    assert complete is False


def test_read_departures_complete(tmp_path):
    path = tmp_path / "departures.csv"
    pd.DataFrame({
        "resource": ["grains"],
        "time_interval": ["AM_peak"],
        "probability": [1.0],
    }).to_csv(path, index=False)
    pairs, complete = read_departures(str(path))
    assert complete is True


def test_read_departures_missing_column_rejected(tmp_path):
    path = tmp_path / "bad.csv"
    pd.DataFrame({"resource": ["a"], "time_interval": ["x"]}).to_csv(path, index=False)
    with pytest.raises(ValueError):
        read_departures(str(path))


def test_read_departures_duplicate_pairs_rejected(tmp_path):
    path = tmp_path / "bad.csv"
    pd.DataFrame({
        "resource": ["a", "a"],
        "time_interval": ["x", "x"],
        "probability": [None, None],
    }).to_csv(path, index=False)
    with pytest.raises(ValueError):
        read_departures(str(path))


def test_read_departures_mixed_probability_rejected(tmp_path):
    path = tmp_path / "bad.csv"
    pd.DataFrame({
        "resource": ["a", "a"],
        "time_interval": ["x", "y"],
        "probability": [1.0, None],
    }).to_csv(path, index=False)
    with pytest.raises(ValueError):
        read_departures(str(path))


def test_departures_need_synthesis_true_when_absent():
    assert departures_need_synthesis(None) is True


def test_departures_need_synthesis_true_when_shape_only():
    assert departures_need_synthesis(([{"resource": "a", "time_interval": "x"}], False)) is True


def test_departures_need_synthesis_false_when_complete():
    assert departures_need_synthesis(([{"resource": "a", "time_interval": "x"}], True)) is False
