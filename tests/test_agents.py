import geopandas as gpd
import pandas as pd
from shapely.geometry import Polygon

from urban_dollop.synth.agents import agents


SUPPLY = pd.DataFrame([
    {"zone": "A", "parcels": 7},
    {"zone": "B", "parcels": 5},
])

DEMAND = pd.DataFrame([
    {"zone": "A", "parcels": 4},
    {"zone": "B", "parcels": 9},
    {"zone": "C", "parcels": 3},
])

BATCH_SIZES = pd.DataFrame([
    {"resource": "parcels", "batch_size": 3, "probability": 1.0},
])

ZONES = gpd.GeoDataFrame(
    {"zone": ["A", "B"]},
    geometry=[
        Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]),
        Polygon([(1, 0), (2, 0), (2, 1), (1, 1)]),
    ],
    crs=None,
)


def test_returns_geodataframe():
    gdf = agents(SUPPLY, DEMAND, BATCH_SIZES, ZONES)
    assert isinstance(gdf, gpd.GeoDataFrame)


def test_has_required_columns():
    gdf = agents(SUPPLY, DEMAND, BATCH_SIZES, ZONES)
    assert "zone" in gdf.columns
    assert "parcels_supply" in gdf.columns
    assert "parcels_demand" in gdf.columns
    assert "geometry" in gdf.columns


def test_skips_stratum_without_zone():
    gdf = agents(SUPPLY, DEMAND, BATCH_SIZES, ZONES)
    assert "C" not in gdf["zone"].values


def test_supply_exhausted():
    gdf = agents(SUPPLY, DEMAND, BATCH_SIZES, ZONES)
    assert gdf[gdf["zone"] == "A"]["parcels_supply"].sum() == 7
    assert gdf[gdf["zone"] == "B"]["parcels_supply"].sum() == 5


def test_demand_exhausted():
    gdf = agents(SUPPLY, DEMAND, BATCH_SIZES, ZONES)
    assert gdf[gdf["zone"] == "A"]["parcels_demand"].sum() == 4
    assert gdf[gdf["zone"] == "B"]["parcels_demand"].sum() == 9


def test_geometries_inside_zones():
    gdf = agents(SUPPLY, DEMAND, BATCH_SIZES, ZONES)
    zone_polys = dict(zip(ZONES["zone"], ZONES.geometry))
    for _, row in gdf.iterrows():
        assert zone_polys[row["zone"]].contains(row["geometry"])


def test_supply_only_resource():
    supply = pd.DataFrame([{"zone": "A", "parcels": 3, "grain": 6}])
    demand = pd.DataFrame([{"zone": "A", "parcels": 3}])
    batch = pd.DataFrame([
        {"resource": "parcels", "batch_size": 3, "probability": 1.0},
        {"resource": "grain", "batch_size": 3, "probability": 1.0},
    ])
    zones = gpd.GeoDataFrame(
        {"zone": ["A"]},
        geometry=[Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])],
        crs=None,
    )
    gdf = agents(supply, demand, batch, zones)
    assert gdf["grain_demand"].sum() == 0
    assert gdf["grain_supply"].sum() == 6


def test_empty_when_no_zone_intersection():
    zones = gpd.GeoDataFrame(
        {"zone": ["Z"]},
        geometry=[Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])],
        crs=None,
    )
    gdf = agents(SUPPLY, DEMAND, BATCH_SIZES, zones)
    assert len(gdf) == 0
