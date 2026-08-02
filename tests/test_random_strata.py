from urban_dollop.helpers.random_strata import random_strata


def test_zero_sigma_is_deterministic_minimal():
    rows = random_strata(sigma=0.0)
    assert rows == [{"stratum_column": "zone_id", "stratum_value": "zone_1", "effect": None}]


def test_always_includes_zone_id():
    rows = random_strata(sigma=1.5)
    columns = {r["stratum_column"] for r in rows}
    assert "zone_id" in columns


def test_effect_always_none():
    rows = random_strata(sigma=1.0)
    assert all(r["effect"] is None for r in rows)
