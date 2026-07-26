from urban_dollop.synth.stratified_resources import stratified_resources


SLOPES = [
    {"stratum_1": "value_1", "slope": -2.0},
    {"stratum_1": "value_2", "slope": 0.0},
    {"stratum_1": "value_3", "slope": 2.0},
]

THRESHOLDS = [
    {"resource": "resource_1", "resource_level": 1, "threshold": -1.0},
    {"resource": "resource_1", "resource_level": 2, "threshold": 0.0},
    {"resource": "resource_1", "resource_level": 3, "threshold": None},
]


def test_returns_one_row_per_stratum():
    rows = stratified_resources(SLOPES, THRESHOLDS)
    assert len(rows) == len(SLOPES)


def test_output_has_stratum_and_resource_cols():
    rows = stratified_resources(SLOPES, THRESHOLDS)
    for row in rows:
        assert "stratum_1" in row
        assert "resource_1" in row
        assert "slope" not in row


def test_counts_are_integers():
    rows = stratified_resources(SLOPES, THRESHOLDS)
    for row in rows:
        assert isinstance(row["resource_1"], int)


def test_higher_slope_gives_higher_count():
    rows = stratified_resources(SLOPES, THRESHOLDS)
    counts = [row["resource_1"] for row in rows]
    assert counts[0] <= counts[1] <= counts[2]


def test_single_level_resource_always_returns_that_level():
    slopes = [{"stratum_1": "value_1", "slope": 999.0}]
    thresholds = [{"resource": "r", "resource_level": 5, "threshold": None}]
    rows = stratified_resources(slopes, thresholds)
    assert rows[0]["r"] == 5
