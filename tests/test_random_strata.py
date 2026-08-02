from urban_dollop.helpers.random_strata import random_strata


def test_zero_sigma_is_deterministic_minimal():
    rows = random_strata(sigma=0.0)
    assert rows == [{
        "stratum": "zone_id",
        "stratum_value": 1,
        "resource_1": None,
    }]


def test_zone_id_values_are_integers():
    rows = random_strata(sigma=1.5)
    zone_values = [r["stratum_value"] for r in rows if r["stratum"] == "zone_id"]
    assert all(isinstance(v, int) for v in zone_values)


def test_non_zone_id_values_are_strings():
    rows = random_strata(sigma=1.5)
    other_values = [r["stratum_value"] for r in rows if r["stratum"] != "zone_id"]
    assert all(isinstance(v, str) for v in other_values)


def test_always_includes_zone_id():
    rows = random_strata(sigma=1.5)
    strata = {r["stratum"] for r in rows}
    assert "zone_id" in strata


def test_resource_columns_always_none():
    rows = random_strata(sigma=1.0)
    for row in rows:
        for key, value in row.items():
            if key not in ("stratum", "stratum_value"):
                assert value is None


def test_one_row_per_stratum_value_all_sharing_the_same_resource_columns():
    rows = random_strata(sigma=1.5)
    strata_pairs = {(r["stratum"], r["stratum_value"]) for r in rows}
    assert len(rows) == len(strata_pairs)
    resource_keysets = {frozenset(r) - {"stratum", "stratum_value"} for r in rows}
    assert len(resource_keysets) == 1
