from urban_dollop.helpers.combine_resources import combine_resources


def _entry(entries, resource, **combo):
    for entry in entries:
        if entry["resource"] == resource and all(entry[k] == v for k, v in combo.items()):
            return entry
    return None


def test_single_dimension_single_resource():
    effects = [
        {"stratum": "zone_id", "stratum_value": 1, "grains": 0.0},
    ]
    thresholds = [
        {"resource": "grains", "resource_level": 0, "threshold": None},
    ]
    entries = combine_resources(effects, thresholds)
    assert len(entries) == 1
    assert entries[0]["zone_id"] == 1
    assert entries[0]["resource"] == "grains"
    assert entries[0]["pmf"] == [(0, 1.0)]


def test_resource_not_in_thresholds_is_excluded():
    effects = [
        {"stratum": "zone_id", "stratum_value": 1, "grains": 0.0, "parcels": 0.0},
    ]
    thresholds = [
        {"resource": "grains", "resource_level": 0, "threshold": None},
    ]
    entries = combine_resources(effects, thresholds)
    resources = {e["resource"] for e in entries}
    assert resources == {"grains"}


def test_resource_not_in_effects_is_excluded():
    effects = [
        {"stratum": "zone_id", "stratum_value": 1, "grains": 0.0},
    ]
    thresholds = [
        {"resource": "grains", "resource_level": 0, "threshold": None},
        {"resource": "parcels", "resource_level": 0, "threshold": None},
    ]
    entries = combine_resources(effects, thresholds)
    resources = {e["resource"] for e in entries}
    assert resources == {"grains"}


def test_missing_effect_for_one_dimension_omits_the_whole_combination():
    effects = [
        {"stratum": "zone_id", "stratum_value": 1, "grains": 0.5},
        {"stratum": "stratum_1", "stratum_value": "value_1", "grains": None},
        {"stratum": "stratum_1", "stratum_value": "value_2", "grains": 0.2},
    ]
    thresholds = [
        {"resource": "grains", "resource_level": 0, "threshold": None},
    ]
    entries = combine_resources(effects, thresholds)
    combos = {(e["zone_id"], e["stratum_1"]) for e in entries}
    assert (1, "value_1") not in combos
    assert (1, "value_2") in combos


def test_beta_zero_gives_uniform_ish_split_around_thresholds():
    effects = [{"stratum": "zone_id", "stratum_value": 1, "grains": 0.0}]
    thresholds = [
        {"resource": "grains", "resource_level": 0, "threshold": 0.0},
        {"resource": "grains", "resource_level": 10, "threshold": None},
    ]
    entries = combine_resources(effects, thresholds)
    pmf = dict(entries[0]["pmf"])
    assert abs(pmf[0] - 0.5) < 1e-9
    assert abs(pmf[10] - 0.5) < 1e-9


def test_single_level_resource_with_nan_threshold_gives_probability_one(tmp_path):
    # regression: pandas-sourced rows use NaN for empty cells, not None --
    # a single-level resource's one row has threshold=NaN (nothing to
    # fill), which must be excluded from the threshold list the same way
    # None is, not fed into logistic() as a real cutpoint.
    import pandas as pd

    from urban_dollop.cli._io import read_computed_thresholds

    effects = [{"stratum": "zone_id", "stratum_value": 1, "grains": 0.5}]
    path = tmp_path / "thresholds.csv"
    pd.DataFrame([{"resource": "grains", "resource_level": 2, "threshold": None}]).to_csv(path, index=False)
    thresholds = read_computed_thresholds(str(path))
    assert isinstance(thresholds[0]["threshold"], float)  # confirms it's real NaN, not None

    entries = combine_resources(effects, thresholds)
    assert entries[0]["pmf"] == [(2, 1.0)]


def test_full_cartesian_product_of_multiple_dimensions():
    effects = [
        {"stratum": "zone_id", "stratum_value": 1, "grains": 0.1},
        {"stratum": "zone_id", "stratum_value": 2, "grains": 0.2},
        {"stratum": "stratum_1", "stratum_value": "a", "grains": 0.3},
        {"stratum": "stratum_1", "stratum_value": "b", "grains": 0.4},
    ]
    thresholds = [
        {"resource": "grains", "resource_level": 0, "threshold": None},
    ]
    entries = combine_resources(effects, thresholds)
    combos = {(e["zone_id"], e["stratum_1"]) for e in entries}
    assert combos == {(1, "a"), (1, "b"), (2, "a"), (2, "b")}
