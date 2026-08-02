from urban_dollop.helpers.random_resources import random_resources


def test_zero_sigma_is_deterministic_minimal_count():
    rows = random_resources(sigma=0.0)
    resources = {r["resource"] for r in rows}
    assert len(resources) == 1
    assert len(rows) == 1


def test_threshold_always_none():
    rows = random_resources(sigma=1.0)
    assert all(r["threshold"] is None for r in rows)


def test_levels_distinct_within_a_resource():
    rows = random_resources(sigma=2.0)
    by_resource = {}
    for row in rows:
        by_resource.setdefault(row["resource"], []).append(row["resource_level"])
    for levels in by_resource.values():
        assert len(levels) == len(set(levels))
