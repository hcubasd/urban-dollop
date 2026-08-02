import pandas as pd
import pytest

from urban_dollop.cli._io import check_sigma_relevant, read_effects, read_thresholds, write_rows


def test_read_effects_none_if_absent(tmp_path):
    assert read_effects(str(tmp_path / "missing.csv")) is None


def test_read_effects_valid_shape_only(tmp_path):
    path = tmp_path / "supply_effects.csv"
    pd.DataFrame([
        {"stratum": "zone_id", "stratum_value": "z1", "parcels": None},
    ]).to_csv(path, index=False)
    rows = read_effects(str(path))
    assert rows[0]["stratum"] == "zone_id"
    assert "parcels" in rows[0]


def test_read_effects_missing_zone_id_rejected(tmp_path):
    path = tmp_path / "bad.csv"
    pd.DataFrame([
        {"stratum": "stratum_1", "stratum_value": "a", "parcels": None},
    ]).to_csv(path, index=False)
    with pytest.raises(ValueError):
        read_effects(str(path))


def test_read_effects_integer_stratum_value_accepted(tmp_path):
    path = tmp_path / "ok.csv"
    pd.DataFrame([
        {"stratum": "zone_id", "stratum_value": 1, "parcels": None},
        {"stratum": "zone_id", "stratum_value": 2, "parcels": None},
    ]).to_csv(path, index=False)
    rows = read_effects(str(path))
    assert [r["stratum_value"] for r in rows] == [1, 2]


def test_read_effects_nonstring_non_zone_id_stratum_value_rejected(tmp_path):
    path = tmp_path / "bad.csv"
    pd.DataFrame([
        {"stratum": "zone_id", "stratum_value": 1, "parcels": None},
        {"stratum": "stratum_1", "stratum_value": 5, "parcels": None},
    ]).to_csv(path, index=False)
    with pytest.raises(ValueError):
        read_effects(str(path))


def test_read_effects_string_non_zone_id_stratum_value_accepted(tmp_path):
    path = tmp_path / "ok.csv"
    pd.DataFrame([
        {"stratum": "zone_id", "stratum_value": 1, "parcels": None},
        {"stratum": "stratum_1", "stratum_value": "value_1", "parcels": None},
    ]).to_csv(path, index=False)
    rows = read_effects(str(path))
    assert rows[1]["stratum_value"] == "value_1"


def test_read_effects_nonfloat_resource_column_rejected(tmp_path):
    path = tmp_path / "bad.csv"
    pd.DataFrame([
        {"stratum": "zone_id", "stratum_value": "z1", "parcels": "not a float"},
    ]).to_csv(path, index=False)
    with pytest.raises(ValueError):
        read_effects(str(path))


def test_read_effects_no_resource_columns_rejected(tmp_path):
    path = tmp_path / "bad.csv"
    pd.DataFrame([
        {"stratum": "zone_id", "stratum_value": "z1"},
    ]).to_csv(path, index=False)
    with pytest.raises(ValueError):
        read_effects(str(path))


def test_read_effects_already_filled_rejected(tmp_path):
    path = tmp_path / "bad.csv"
    pd.DataFrame([
        {"stratum": "zone_id", "stratum_value": "z1", "parcels": 0.5},
    ]).to_csv(path, index=False)
    with pytest.raises(ValueError):
        read_effects(str(path))


def test_read_effects_partially_filled_rejected(tmp_path):
    path = tmp_path / "bad.csv"
    pd.DataFrame([
        {"stratum": "zone_id", "stratum_value": "z1", "parcels": 0.5},
        {"stratum": "zone_id", "stratum_value": "z2", "parcels": None},
    ]).to_csv(path, index=False)
    with pytest.raises(ValueError):
        read_effects(str(path))


def test_read_effects_one_resource_column_filled_another_empty_rejected(tmp_path):
    path = tmp_path / "bad.csv"
    pd.DataFrame([
        {"stratum": "zone_id", "stratum_value": "z1", "parcels": 0.5, "pallets": None},
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


def test_read_thresholds_nonstring_resource_rejected(tmp_path):
    path = tmp_path / "bad.csv"
    pd.DataFrame([
        {"resource": 1, "resource_level": 1, "threshold": None},
        {"resource": 2, "resource_level": 1, "threshold": None},
    ]).to_csv(path, index=False)
    with pytest.raises(ValueError):
        read_thresholds(str(path))


def test_read_thresholds_nonint_resource_level_rejected(tmp_path):
    path = tmp_path / "bad.csv"
    pd.DataFrame([
        {"resource": "parcels", "resource_level": 1.5, "threshold": None},
    ]).to_csv(path, index=False)
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


def test_check_sigma_relevant_ok_when_nothing_exists():
    check_sigma_relevant(None, sigma_given=True, path="x.csv")
    check_sigma_relevant(None, sigma_given=False, path="x.csv")


def test_check_sigma_relevant_ok_when_file_exists_but_sigma_not_given():
    check_sigma_relevant([{"a": 1}], sigma_given=False, path="x.csv")


def test_check_sigma_relevant_throws_when_file_exists_and_sigma_given():
    with pytest.raises(ValueError):
        check_sigma_relevant([{"a": 1}], sigma_given=True, path="x.csv")
