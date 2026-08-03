import geopandas as gpd
from shapely.geometry import Polygon

from urban_dollop.helpers.combine_agent_inputs import combine_agent_inputs

SQUARE = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])


def _zones(zone_ids, geoms=None):
    if geoms is None:
        geoms = [SQUARE] * len(zone_ids)
    return gpd.GeoDataFrame({"zone_id": zone_ids, "geometry": geoms})


def test_basic_match():
    supply = [{"zone_id": 1, "grains": 10}]
    demand = [{"zone_id": 1, "grains": 8}]
    capacities = [{"zone_id": 1, "resource": "grains", "resource_level": 0, "probability": 1.0}]
    needs = [{"zone_id": 1, "resource": "grains", "resource_level": 0, "probability": 1.0}]
    contexts = combine_agent_inputs(supply, demand, capacities, needs, _zones([1]))
    assert len(contexts) == 1
    assert contexts[0]["dims"] == {"zone_id": 1}
    assert contexts[0]["resources"]["grains"]["supply"] == 10
    assert contexts[0]["resources"]["grains"]["demand"] == 8


def test_resource_missing_on_one_side_excludes_it():
    supply = [{"zone_id": 1, "grains": 10, "parcels": 3}]
    demand = [{"zone_id": 1, "grains": 8}]  # no parcels
    capacities = [
        {"zone_id": 1, "resource": "grains", "resource_level": 0, "probability": 1.0},
        {"zone_id": 1, "resource": "parcels", "resource_level": 0, "probability": 1.0},
    ]
    needs = [
        {"zone_id": 1, "resource": "grains", "resource_level": 0, "probability": 1.0},
        {"zone_id": 1, "resource": "parcels", "resource_level": 0, "probability": 1.0},
    ]
    contexts = combine_agent_inputs(supply, demand, capacities, needs, _zones([1]))
    assert set(contexts[0]["resources"]) == {"grains"}


def test_mismatched_dimension_sets_give_empty_result():
    supply = [{"zone_id": 1, "stratum_1": "a", "grains": 10}]
    demand = [{"zone_id": 1, "grains": 8}]  # no stratum_1 at all
    capacities = [{"zone_id": 1, "resource": "grains", "resource_level": 0, "probability": 1.0}]
    needs = [{"zone_id": 1, "resource": "grains", "resource_level": 0, "probability": 1.0}]
    contexts = combine_agent_inputs(supply, demand, capacities, needs, _zones([1]))
    assert contexts == []


def test_zone_id_type_mismatch_still_matches_via_normalization():
    supply = [{"zone_id": "1", "grains": 10}]  # stringified, as could happen via CSV coercion
    demand = [{"zone_id": 1, "grains": 8}]
    capacities = [{"zone_id": 1, "resource": "grains", "resource_level": 0, "probability": 1.0}]
    needs = [{"zone_id": 1, "resource": "grains", "resource_level": 0, "probability": 1.0}]
    contexts = combine_agent_inputs(supply, demand, capacities, needs, _zones([1]))
    assert len(contexts) == 1


def test_zone_with_null_geometry_is_excluded():
    supply = [{"zone_id": 1, "grains": 10}]
    demand = [{"zone_id": 1, "grains": 8}]
    capacities = [{"zone_id": 1, "resource": "grains", "resource_level": 0, "probability": 1.0}]
    needs = [{"zone_id": 1, "resource": "grains", "resource_level": 0, "probability": 1.0}]
    contexts = combine_agent_inputs(supply, demand, capacities, needs, _zones([1], geoms=[None]))
    assert contexts == []


def test_stratum_missing_entirely_from_one_file_excluded():
    supply = [{"zone_id": 1, "grains": 10}, {"zone_id": 2, "grains": 5}]
    demand = [{"zone_id": 1, "grains": 8}]  # zone 2 missing entirely
    capacities = [
        {"zone_id": 1, "resource": "grains", "resource_level": 0, "probability": 1.0},
        {"zone_id": 2, "resource": "grains", "resource_level": 0, "probability": 1.0},
    ]
    needs = [
        {"zone_id": 1, "resource": "grains", "resource_level": 0, "probability": 1.0},
        {"zone_id": 2, "resource": "grains", "resource_level": 0, "probability": 1.0},
    ]
    contexts = combine_agent_inputs(supply, demand, capacities, needs, _zones([1, 2]))
    assert len(contexts) == 1
    assert contexts[0]["dims"] == {"zone_id": 1}
