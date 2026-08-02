import pandas as pd
import pytest

from urban_dollop.cli._io import read_effects, read_thresholds, write_rows


def test_read_effects_none_if_absent(tmp_path):
    assert read_effects(str(tmp_path / "missing.csv")) is None


def test_read_effects_valid_shape_only(tmp_path):
    path = tmp_path / "supply_effects.csv"
    pd.DataFrame([
        {"stratum_column": "zone_id", "stratum_value": "z1", "effect": None},
    ]).to_csv(path, index=False)
    rows = read_effects(str(path))
    assert rows[0]["stratum_column"] == "zone_id"


def test_read_effects_missing_zone_id_rejected(tmp_path):
    path = tmp_path / "bad.csv"
    pd.DataFrame([
        {"stratum_column": "stratum_1", "stratum_value": "a", "effect": None},
    ]).to_csv(path, index=False)
    with pytest.raises(ValueError):
        read_effects(str(path))


def test_read_effects_nonstring_stratum_value_rejected(tmp_path):
    path = tmp_path / "bad.csv"
    pd.DataFrame([
        {"stratum_column": "zone_id", "stratum_value": 1, "effect": None},
        {"stratum_column": "zone_id", "stratum_value": 2, "effect": None},
    ]).to_csv(path, index=False)
    with pytest.raises(ValueError):
        read_effects(str(path))


def test_read_effects_already_filled_rejected(tmp_path):
    path = tmp_path / "bad.csv"
    pd.DataFrame([
        {"stratum_column": "zone_id", "stratum_value": "z1", "effect": 0.5},
    ]).to_csv(path, index=False)
    with pytest.raises(ValueError):
        read_effects(str(path))


def test_read_effects_partially_filled_rejected(tmp_path):
    path = tmp_path / "bad.csv"
    pd.DataFrame([
        {"stratum_column": "zone_id", "stratum_value": "z1", "effect": 0.5},
        {"stratum_column": "zone_id", "stratum_value": "z2", "effect": None},
    ]).to_csv(path, index=False)
    with pytest.raises(ValueError):
        read_effects(str(path))


def test_read_thresholds_none_if_absent(tmp_path):
    assert read_thresholds(str(tmp_path / "missing.csv")) is None


def test_read_thresholds_valid_shape_only(tmp_path):
    path = tmp_path / "supply_thresholds.csv"
    pd.DataFrame([
        {"resource": "parcels", "resource_level": 1, "threshold": None},
    ]).to_csv(path, index=False)
    rows = read_thresholds(str(path))
    assert rows[0]["resource"] == "parcels"


def test_read_thresholds_wrong_columns_rejected(tmp_path):
    path = tmp_path / "bad.csv"
    pd.DataFrame([{"resource": "parcels", "threshold": None}]).to_csv(path, index=False)
    with pytest.raises(ValueError):
        read_thresholds(str(path))


def test_read_thresholds_already_filled_rejected(tmp_path):
    path = tmp_path / "bad.csv"
    pd.DataFrame([
        {"resource": "parcels", "resource_level": 1, "threshold": 0.2},
    ]).to_csv(path, index=False)
    with pytest.raises(ValueError):
        read_thresholds(str(path))


def test_write_rows_round_trips(tmp_path):
    path = tmp_path / "out.csv"
    rows = [{"resource": "parcels", "resource_level": 1, "threshold": 0.2}]
    write_rows(rows, str(path))
    assert pd.read_csv(path).to_dict("records") == rows
