import pandas as pd
import pytest

from urban_dollop.cli._io import (
    check_sigma_relevant,
    effects_need_synthesis,
    load_effects_and_thresholds,
    read_computed_thresholds,
    read_effects,
    read_thresholds,
    write_rows,
)


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


def test_read_effects_already_filled_accepted(tmp_path):
    path = tmp_path / "ok.csv"
    pd.DataFrame([
        {"stratum": "zone_id", "stratum_value": "z1", "parcels": 0.5},
    ]).to_csv(path, index=False)
    rows = read_effects(str(path))
    assert rows[0]["parcels"] == 0.5


def test_read_effects_partially_filled_accepted(tmp_path):
    path = tmp_path / "ok.csv"
    pd.DataFrame([
        {"stratum": "zone_id", "stratum_value": "z1", "parcels": 0.5},
        {"stratum": "zone_id", "stratum_value": "z2", "parcels": None},
    ]).to_csv(path, index=False)
    rows = read_effects(str(path))
    assert rows[0]["parcels"] == 0.5
    assert pd.isna(rows[1]["parcels"])


def test_read_effects_one_resource_column_filled_another_empty_accepted(tmp_path):
    path = tmp_path / "ok.csv"
    pd.DataFrame([
        {"stratum": "zone_id", "stratum_value": "z1", "parcels": 0.5, "pallets": None},
    ]).to_csv(path, index=False)
    rows = read_effects(str(path))
    assert rows[0]["parcels"] == 0.5
    assert pd.isna(rows[0]["pallets"])


def test_effects_need_synthesis_true_when_absent():
    assert effects_need_synthesis(None) is True


def test_effects_need_synthesis_true_when_entirely_empty():
    rows = [
        {"stratum": "zone_id", "stratum_value": "z1", "parcels": None, "pallets": None},
        {"stratum": "zone_id", "stratum_value": "z2", "parcels": None, "pallets": None},
    ]
    assert effects_need_synthesis(rows) is True


def test_effects_need_synthesis_false_when_any_value_set():
    rows = [
        {"stratum": "zone_id", "stratum_value": "z1", "parcels": 0.5, "pallets": None},
        {"stratum": "zone_id", "stratum_value": "z2", "parcels": None, "pallets": None},
    ]
    assert effects_need_synthesis(rows) is False


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


def test_read_computed_thresholds_none_if_absent(tmp_path):
    assert read_computed_thresholds(str(tmp_path / "missing.csv")) is None


def test_read_computed_thresholds_returns_rows_when_filled(tmp_path):
    path = tmp_path / "filled.csv"
    pd.DataFrame([
        {"resource": "parcels", "resource_level": 1, "threshold": 0.2},
        {"resource": "parcels", "resource_level": 2, "threshold": None},
    ]).to_csv(path, index=False)
    rows = read_computed_thresholds(str(path))
    assert rows[0]["threshold"] == 0.2


def test_read_computed_thresholds_single_level_resource_is_ready(tmp_path):
    path = tmp_path / "single_level.csv"
    pd.DataFrame([
        {"resource": "parcels", "resource_level": 1, "threshold": None},
    ]).to_csv(path, index=False)
    rows = read_computed_thresholds(str(path))
    assert rows is not None


def test_read_computed_thresholds_multi_level_shape_only_not_ready(tmp_path):
    path = tmp_path / "multi_shape_only.csv"
    pd.DataFrame([
        {"resource": "parcels", "resource_level": 1, "threshold": None},
        {"resource": "parcels", "resource_level": 2, "threshold": None},
        {"resource": "parcels", "resource_level": 3, "threshold": None},
    ]).to_csv(path, index=False)
    assert read_computed_thresholds(str(path)) is None


def test_read_computed_thresholds_still_validates_structure(tmp_path):
    path = tmp_path / "bad.csv"
    pd.DataFrame([{"resource": "parcels", "threshold": None}]).to_csv(path, index=False)
    with pytest.raises(ValueError):
        read_computed_thresholds(str(path))


def test_load_effects_and_thresholds_ok(tmp_path):
    effects_path = tmp_path / "effects.csv"
    thresholds_path = tmp_path / "thresholds.csv"
    pd.DataFrame([
        {"stratum": "zone_id", "stratum_value": 1, "parcels": 0.5},
    ]).to_csv(effects_path, index=False)
    pd.DataFrame([
        {"resource": "parcels", "resource_level": 1, "threshold": None},
    ]).to_csv(thresholds_path, index=False)
    effects_rows, thresholds_rows = load_effects_and_thresholds(str(effects_path), str(thresholds_path))
    assert effects_rows[0]["parcels"] == 0.5
    assert thresholds_rows[0]["resource"] == "parcels"


def test_load_effects_and_thresholds_raises_when_effects_not_ready(tmp_path):
    effects_path = tmp_path / "missing_effects.csv"
    thresholds_path = tmp_path / "thresholds.csv"
    pd.DataFrame([
        {"resource": "parcels", "resource_level": 1, "threshold": None},
    ]).to_csv(thresholds_path, index=False)
    with pytest.raises(ValueError):
        load_effects_and_thresholds(str(effects_path), str(thresholds_path))


def test_load_effects_and_thresholds_raises_when_thresholds_not_ready(tmp_path):
    effects_path = tmp_path / "effects.csv"
    thresholds_path = tmp_path / "missing_thresholds.csv"
    pd.DataFrame([
        {"stratum": "zone_id", "stratum_value": 1, "parcels": 0.5},
    ]).to_csv(effects_path, index=False)
    with pytest.raises(ValueError):
        load_effects_and_thresholds(str(effects_path), str(thresholds_path))


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
