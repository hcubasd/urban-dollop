from urban_dollop.helpers.fill_thresholds import fill_thresholds


def test_fills_sorted_by_level_last_gets_none():
    rows = [
        {"resource": "parcels", "resource_level": 20, "threshold": None},
        {"resource": "parcels", "resource_level": 1, "threshold": None},
        {"resource": "parcels", "resource_level": 5, "threshold": None},
    ]
    filled = fill_thresholds(rows)
    by_level = {r["resource_level"]: r["threshold"] for r in filled}
    assert by_level[20] is None
    assert by_level[1] is not None
    assert by_level[5] is not None
    assert by_level[1] <= by_level[5]


def test_single_level_gets_no_threshold():
    rows = [{"resource": "parcels", "resource_level": 7, "threshold": None}]
    filled = fill_thresholds(rows)
    assert filled == [{"resource": "parcels", "resource_level": 7, "threshold": None}]


def test_independent_across_resources():
    rows = [
        {"resource": "parcels", "resource_level": 1, "threshold": None},
        {"resource": "parcels", "resource_level": 2, "threshold": None},
        {"resource": "pallets", "resource_level": 1, "threshold": None},
    ]
    filled = fill_thresholds(rows)
    assert len(filled) == 3
