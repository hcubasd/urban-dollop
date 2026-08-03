import geopandas as gpd
from shapely.geometry import Polygon

from urban_dollop.synth.agents import agents

SQUARE = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])


def _zones(zone_ids):
    return gpd.GeoDataFrame({"zone_id": zone_ids, "geometry": [SQUARE] * len(zone_ids)})


def test_no_contexts_gives_no_agents():
    rows = agents([], [], [], [], _zones([]))
    assert rows == []


def test_depletes_toward_zero_and_halts():
    supply = [{"zone_id": 1, "grains": 10}]
    demand = [{"zone_id": 1, "grains": 8}]
    capacities = [
        {"zone_id": 1, "resource": "grains", "resource_level": 0, "probability": 0.5},
        {"zone_id": 1, "resource": "grains", "resource_level": 5, "probability": 0.5},
    ]
    needs = [
        {"zone_id": 1, "resource": "grains", "resource_level": 0, "probability": 0.3},
        {"zone_id": 1, "resource": "grains", "resource_level": 4, "probability": 0.7},
    ]
    rows = agents(supply, demand, capacities, needs, _zones([1]))
    assert len(rows) >= 1
    assert sum(r["grains_capacity"] for r in rows) <= 10
    assert sum(r["grains_need"] for r in rows) <= 8
    for r in rows:
        assert r["grains_capacity"] in (0, 5)
        assert r["grains_need"] in (0, 4)
        assert SQUARE.contains(r["geometry"])
        assert "agent_id" in r
        assert r["zone_id"] == 1


def test_degenerate_zero_distribution_halts_after_one_agent():
    supply = [{"zone_id": 1, "grains": 10}]
    demand = [{"zone_id": 1, "grains": 10}]
    capacities = [{"zone_id": 1, "resource": "grains", "resource_level": 0, "probability": 1.0}]
    needs = [{"zone_id": 1, "resource": "grains", "resource_level": 0, "probability": 1.0}]
    rows = agents(supply, demand, capacities, needs, _zones([1]))
    assert len(rows) == 1
    assert rows[0]["grains_capacity"] == 0
    assert rows[0]["grains_need"] == 0


def test_agent_ids_unique_and_increasing():
    supply = [{"zone_id": 1, "grains": 20}]
    demand = [{"zone_id": 1, "grains": 20}]
    capacities = [{"zone_id": 1, "resource": "grains", "resource_level": 1, "probability": 1.0}]
    needs = [{"zone_id": 1, "resource": "grains", "resource_level": 1, "probability": 1.0}]
    rows = agents(supply, demand, capacities, needs, _zones([1]))
    ids = [r["agent_id"] for r in rows]
    assert ids == sorted(ids)
    assert len(ids) == len(set(ids))
