import pandas as pd
import pytest

from urban_dollop.cli.synth_emission_factors import (
    read_emission_factors,
    emission_factors_need_synthesis,
)


def test_read_emission_factors_none_if_absent(tmp_path):
    assert read_emission_factors(str(tmp_path / "missing.csv")) is None


def test_read_emission_factors_shape_only(tmp_path):
    path = tmp_path / "emission_factors.csv"
    pd.DataFrame({
        "vehicle_type": ["hdv", "ldv"],
        "pollutant": ["pm10", "pm25"],
        "emission_factor": [None, None],
    }).to_csv(path, index=False)
    pairs, complete = read_emission_factors(str(path))
    assert pairs == [
        {"vehicle_type": "hdv", "pollutant": "pm10"},
        {"vehicle_type": "ldv", "pollutant": "pm25"},
    ]
    assert complete is False


def test_read_emission_factors_complete(tmp_path):
    path = tmp_path / "emission_factors.csv"
    pd.DataFrame({
        "vehicle_type": ["hdv"],
        "pollutant": ["pm10"],
        "emission_factor": [0.5],
    }).to_csv(path, index=False)
    pairs, complete = read_emission_factors(str(path))
    assert complete is True


def test_read_emission_factors_missing_column_rejected(tmp_path):
    path = tmp_path / "bad.csv"
    pd.DataFrame({"vehicle_type": ["hdv"], "pollutant": ["pm10"]}).to_csv(path, index=False)
    with pytest.raises(ValueError):
        read_emission_factors(str(path))


def test_read_emission_factors_duplicate_pairs_rejected(tmp_path):
    path = tmp_path / "bad.csv"
    pd.DataFrame({
        "vehicle_type": ["hdv", "hdv"],
        "pollutant": ["pm10", "pm10"],
        "emission_factor": [None, None],
    }).to_csv(path, index=False)
    with pytest.raises(ValueError):
        read_emission_factors(str(path))


def test_read_emission_factors_mixed_rejected(tmp_path):
    path = tmp_path / "bad.csv"
    pd.DataFrame({
        "vehicle_type": ["hdv", "ldv"],
        "pollutant": ["pm10", "pm25"],
        "emission_factor": [0.5, None],
    }).to_csv(path, index=False)
    with pytest.raises(ValueError):
        read_emission_factors(str(path))


def test_emission_factors_need_synthesis_true_when_absent():
    assert emission_factors_need_synthesis(None) is True


def test_emission_factors_need_synthesis_true_when_shape_only():
    assert emission_factors_need_synthesis(([{"vehicle_type": "a", "pollutant": "b"}], False)) is True


def test_emission_factors_need_synthesis_false_when_complete():
    assert emission_factors_need_synthesis(([{"vehicle_type": "a", "pollutant": "b"}], True)) is False
