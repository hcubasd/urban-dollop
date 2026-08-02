import pytest

from urban_dollop.synth.capacity_thresholds import capacity_thresholds
from urban_dollop.synth.demand_thresholds import demand_thresholds
from urban_dollop.synth.need_thresholds import need_thresholds
from urban_dollop.synth.supply_thresholds import supply_thresholds

FUNCTIONS = [supply_thresholds, demand_thresholds, capacity_thresholds, need_thresholds]


@pytest.mark.parametrize("thresholds", FUNCTIONS)
def test_nothing_given_synthesizes_shape_and_values(thresholds):
    rows = thresholds(sigma=0.0)
    assert len(rows) == 1
    assert rows[0]["threshold"] is None


@pytest.mark.parametrize("thresholds", FUNCTIONS)
def test_given_shape_only_values_get_filled(thresholds):
    rows = [
        {"resource": "parcels", "resource_level": 20, "threshold": None},
        {"resource": "parcels", "resource_level": 1, "threshold": None},
    ]
    filled = thresholds(rows)
    by_level = {r["resource_level"]: r["threshold"] for r in filled}
    assert by_level[1] is not None
    assert by_level[20] is None
