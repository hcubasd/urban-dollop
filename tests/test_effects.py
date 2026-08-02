import pytest

from urban_dollop.synth.capacity_effects import capacity_effects
from urban_dollop.synth.demand_effects import demand_effects
from urban_dollop.synth.need_effects import need_effects
from urban_dollop.synth.supply_effects import supply_effects

FUNCTIONS = [supply_effects, demand_effects, capacity_effects, need_effects]


@pytest.mark.parametrize("effects", FUNCTIONS)
def test_nothing_given_synthesizes_shape_and_values(effects):
    rows = effects(sigma=0.0)
    assert rows == [{
        "stratum": "zone_id",
        "stratum_value": 1,
        "resource_1": rows[0]["resource_1"],
    }]
    assert isinstance(rows[0]["resource_1"], float)


@pytest.mark.parametrize("effects", FUNCTIONS)
def test_given_shape_only_values_get_filled(effects):
    rows = [
        {"stratum": "zone_id", "stratum_value": "downtown", "parcels": None},
        {"stratum": "zone_id", "stratum_value": "suburb", "parcels": None},
    ]
    filled = effects(rows)
    assert [r["stratum_value"] for r in filled] == ["downtown", "suburb"]
    assert all(isinstance(r["parcels"], float) for r in filled)


@pytest.mark.parametrize("effects", FUNCTIONS)
def test_given_shape_preserved_exactly_no_extra_rows_invented(effects):
    rows = [{"stratum": "zone_id", "stratum_value": "z1", "parcels": None}]
    filled = effects(rows)
    assert len(filled) == 1


@pytest.mark.parametrize("effects", FUNCTIONS)
def test_multiple_resource_columns_all_get_filled(effects):
    rows = [{"stratum": "zone_id", "stratum_value": "z1", "parcels": None, "pallets": None}]
    filled = effects(rows)
    assert isinstance(filled[0]["parcels"], float)
    assert isinstance(filled[0]["pallets"], float)


@pytest.mark.parametrize("effects", FUNCTIONS)
def test_pure_synthesis_fills_every_present_cell_and_can_be_sparse(effects):
    saw_sparse = False
    for _ in range(30):
        rows = effects(sigma=1.5)
        resource_cols = {c for row in rows for c in row if c not in ("stratum", "stratum_value")}
        for row in rows:
            for col in resource_cols:
                if col in row:
                    assert isinstance(row[col], float)
            if len(row) - 2 < len(resource_cols):
                saw_sparse = True
    assert saw_sparse
