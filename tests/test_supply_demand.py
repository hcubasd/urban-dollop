import pytest

from urban_dollop.synth.demand import demand
from urban_dollop.synth.supply import supply

FUNCTIONS = [supply, demand]

EFFECTS = [
    {"stratum": "zone_id", "stratum_value": 1, "grains": 0.5, "parcels": -0.2},
    {"stratum": "zone_id", "stratum_value": 2, "grains": -0.1},
]
THRESHOLDS = [
    {"resource": "grains", "resource_level": 0, "threshold": -0.3},
    {"resource": "grains", "resource_level": 5, "threshold": 0.4},
    {"resource": "grains", "resource_level": 10, "threshold": None},
    {"resource": "parcels", "resource_level": 0, "threshold": None},
]


@pytest.mark.parametrize("combine", FUNCTIONS)
def test_one_row_per_stratum_combination(combine):
    rows = combine(EFFECTS, THRESHOLDS)
    assert len(rows) == 2
    zone_ids = {r["zone_id"] for r in rows}
    assert zone_ids == {1, 2}


@pytest.mark.parametrize("combine", FUNCTIONS)
def test_values_are_rounded_ints(combine):
    rows = combine(EFFECTS, THRESHOLDS)
    for row in rows:
        for resource in ("grains", "parcels"):
            if resource in row:
                assert isinstance(row[resource], int)


@pytest.mark.parametrize("combine", FUNCTIONS)
def test_resource_missing_for_a_stratum_is_omitted_not_zero(combine):
    rows = combine(EFFECTS, THRESHOLDS)
    zone_2 = next(r for r in rows if r["zone_id"] == 2)
    assert "parcels" not in zone_2


@pytest.mark.parametrize("combine", FUNCTIONS)
def test_computed_zero_stays_explicit(combine):
    rows = combine(EFFECTS, THRESHOLDS)
    zone_1 = next(r for r in rows if r["zone_id"] == 1)
    # parcels has a single level (0) for zone_1 -- a fully-defined, deterministic 0
    assert zone_1["parcels"] == 0
