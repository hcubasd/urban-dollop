import pytest

from urban_dollop.synth.capacities import capacities
from urban_dollop.synth.needs import needs

FUNCTIONS = [capacities, needs]

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
def test_long_format_one_row_per_level(combine):
    rows = combine(EFFECTS, THRESHOLDS)
    zone_1_grains = [r for r in rows if r["zone_id"] == 1 and r["resource"] == "grains"]
    assert len(zone_1_grains) == 3
    assert {r["resource_level"] for r in zone_1_grains} == {0, 5, 10}


@pytest.mark.parametrize("combine", FUNCTIONS)
def test_probabilities_sum_to_one_per_combination_and_resource(combine):
    rows = combine(EFFECTS, THRESHOLDS)
    zone_1_grains = [r for r in rows if r["zone_id"] == 1 and r["resource"] == "grains"]
    assert abs(sum(r["probability"] for r in zone_1_grains) - 1.0) < 1e-9


@pytest.mark.parametrize("combine", FUNCTIONS)
def test_resource_missing_for_a_stratum_has_no_rows(combine):
    rows = combine(EFFECTS, THRESHOLDS)
    zone_2_parcels = [r for r in rows if r["zone_id"] == 2 and r["resource"] == "parcels"]
    assert zone_2_parcels == []


@pytest.mark.parametrize("combine", FUNCTIONS)
def test_single_level_resource_gets_probability_one(combine):
    rows = combine(EFFECTS, THRESHOLDS)
    zone_1_parcels = [r for r in rows if r["zone_id"] == 1 and r["resource"] == "parcels"]
    assert len(zone_1_parcels) == 1
    assert zone_1_parcels[0]["resource_level"] == 0
    assert zone_1_parcels[0]["probability"] == 1.0
