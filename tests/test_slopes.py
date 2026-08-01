from urban_dollop.synth.slopes import random_strata, slopes


def test_one_row_per_column_value_pair():
    rows = slopes({"zone_id": ["zone_1", "zone_2"], "resource": ["resource_1"]})
    assert len(rows) == 3
    pairs = {(r["stratum_column"], r["stratum_value"]) for r in rows}
    assert pairs == {
        ("zone_id", "zone_1"),
        ("zone_id", "zone_2"),
        ("resource", "resource_1"),
    }


def test_slope_is_float():
    rows = slopes({"zone_id": ["zone_1"]})
    assert isinstance(rows[0]["slope"], float)


def test_slopes_are_not_all_identical():
    rows = slopes({"zone_id": [f"zone_{i}" for i in range(20)]})
    assert len({r["slope"] for r in rows}) > 1


def test_no_columns_given_yields_no_rows():
    assert slopes({}) == []


def test_random_strata_always_has_zone_id():
    strata = random_strata(sigma=1.0)
    assert "zone_id" in strata
    assert len(strata["zone_id"]) >= 1


def test_random_strata_zero_sigma_is_deterministic_minimal():
    strata = random_strata(sigma=0.0)
    assert strata == {"zone_id": ["zone_1"]}


def test_random_strata_accepts_supplied_zone_id():
    strata = random_strata(sigma=0.0, zone_id=["borrowed_1", "borrowed_2"])
    assert strata == {"zone_id": ["borrowed_1", "borrowed_2"]}


def test_random_strata_other_dims_are_generic():
    strata = random_strata(sigma=2.0)
    for name in strata:
        if name == "zone_id":
            continue
        assert name.startswith("stratum_")
        assert all(v.startswith("value_") for v in strata[name])
