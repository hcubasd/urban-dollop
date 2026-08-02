from urban_dollop.helpers.fill_value import fill_value


def test_fills_only_none_entries():
    rows = [
        {"stratum_column": "zone_id", "stratum_value": "z1", "effect": None},
        {"stratum_column": "zone_id", "stratum_value": "z2", "effect": 0.5},
    ]
    filled = fill_value(rows, "effect")
    assert filled[0]["effect"] is not None
    assert isinstance(filled[0]["effect"], float)
    assert filled[1]["effect"] == 0.5


def test_does_not_mutate_input():
    rows = [{"stratum_column": "zone_id", "stratum_value": "z1", "effect": None}]
    fill_value(rows, "effect")
    assert rows[0]["effect"] is None


def test_treats_nan_as_empty():
    rows = [{"stratum_column": "zone_id", "stratum_value": "z1", "effect": float("nan")}]
    filled = fill_value(rows, "effect")
    assert filled[0]["effect"] == filled[0]["effect"]  # not NaN anymore


def test_leaves_rows_missing_the_field_entirely_untouched():
    rows = [{"stratum_column": "zone_id", "stratum_value": "z1"}]
    filled = fill_value(rows, "effect")
    assert "effect" not in filled[0]
