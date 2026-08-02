from urban_dollop.helpers.random_strata import random_strata


def test_zero_sigma_is_deterministic_minimal():
    rows = random_strata(sigma=0.0)
    assert rows == [{
        "stratum": "zone_id",
        "stratum_value": "zone_1",
        "resource": "resource_1",
        "effect": None,
    }]


def test_always_includes_zone_id():
    rows = random_strata(sigma=1.5)
    columns = {r["stratum"] for r in rows}
    assert "zone_id" in columns


def test_effect_always_none():
    rows = random_strata(sigma=1.0)
    assert all(r["effect"] is None for r in rows)


def test_every_stratum_value_crossed_with_every_resource():
    rows = random_strata(sigma=1.5)
    strata_pairs = {(r["stratum"], r["stratum_value"]) for r in rows}
    resources = {r["resource"] for r in rows}
    assert len(rows) == len(strata_pairs) * len(resources)
