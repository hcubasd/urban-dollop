import pytest

from urban_dollop.synth.capacity_effects import capacity_effects
from urban_dollop.synth.demand_effects import demand_effects
from urban_dollop.synth.need_effects import need_effects
from urban_dollop.synth.supply_effects import supply_effects

FUNCTIONS = [supply_effects, demand_effects, capacity_effects, need_effects]


@pytest.mark.parametrize("effects", FUNCTIONS)
def test_nothing_given_synthesizes_shape_and_values(effects):
    rows = effects(sigma=0.0)
    assert rows == [{"stratum_column": "zone_id", "stratum_value": "zone_1", "effect": rows[0]["effect"]}]
    assert isinstance(rows[0]["effect"], float)


@pytest.mark.parametrize("effects", FUNCTIONS)
def test_given_shape_only_values_get_filled(effects):
    rows = [
        {"stratum_column": "zone_id", "stratum_value": "downtown", "effect": None},
        {"stratum_column": "zone_id", "stratum_value": "suburb", "effect": None},
    ]
    filled = effects(rows)
    assert [r["stratum_value"] for r in filled] == ["downtown", "suburb"]
    assert all(isinstance(r["effect"], float) for r in filled)


@pytest.mark.parametrize("effects", FUNCTIONS)
def test_given_shape_preserved_exactly_no_extra_dims_invented(effects):
    rows = [{"stratum_column": "zone_id", "stratum_value": "z1", "effect": None}]
    filled = effects(rows)
    assert len(filled) == 1
