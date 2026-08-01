import pytest

from urban_dollop.synth.thresholds import random_resources, thresholds


def test_one_row_per_level():
    rows = thresholds({"resource_1": [1, 2, 3]})
    assert len(rows) == 3
    assert {r["resource_level"] for r in rows} == {1, 2, 3}
    assert all(r["resource"] == "resource_1" for r in rows)


def test_levels_sorted_and_last_has_no_threshold():
    rows = thresholds({"resource_1": [3, 1, 2]})
    by_level = sorted(rows, key=lambda r: r["resource_level"])
    assert by_level[-1]["threshold"] is None
    assert all(r["threshold"] is not None for r in by_level[:-1])


def test_thresholds_ascending():
    rows = thresholds({"resource_1": list(range(10))})
    mus = [r["threshold"] for r in sorted(rows, key=lambda r: r["resource_level"]) if r["threshold"] is not None]
    assert mus == sorted(mus)


def test_single_level_has_no_threshold_and_no_crash():
    rows = thresholds({"resource_1": [5]})
    assert len(rows) == 1
    assert rows[0]["threshold"] is None


def test_multiple_resources_independent():
    rows = thresholds({"resource_1": [1, 2], "resource_2": [1, 2, 3]})
    assert len(rows) == 5


def test_duplicate_levels_rejected():
    with pytest.raises(ValueError):
        thresholds({"resource_1": [1, 1, 2]})


def test_random_resources_always_has_at_least_one():
    resources = random_resources(sigma=1.0)
    assert len(resources) >= 1
    for levels in resources.values():
        assert len(levels) == len(set(levels))


def test_random_resources_zero_sigma_gives_one_resource_one_level():
    resources = random_resources(sigma=0.0)
    assert len(resources) == 1
    (levels,) = resources.values()
    assert len(levels) == 1
