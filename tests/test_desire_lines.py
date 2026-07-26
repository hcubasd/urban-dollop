import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import Point

from urban_dollop.synth.desire_lines import desire_lines


AGENTS = gpd.GeoDataFrame(
    [
        {"parcels_supply": 6, "parcels_demand": 0, "geometry": Point(0.25, 0.25)},
        {"parcels_supply": 0, "parcels_demand": 9, "geometry": Point(0.75, 0.75)},
        {"parcels_supply": 3, "parcels_demand": 0, "geometry": Point(0.25, 0.75)},
        {"parcels_supply": 0, "parcels_demand": 6, "geometry": Point(0.75, 0.25)},
    ],
    crs=None,
)

BATCH_SIZES = pd.DataFrame([
    {"resource": "parcels", "batch_size": 3, "probability": 1.0},
])


def test_returns_geodataframe():
    gdf = desire_lines(AGENTS, BATCH_SIZES)
    assert isinstance(gdf, gpd.GeoDataFrame)


def test_has_required_columns():
    gdf = desire_lines(AGENTS, BATCH_SIZES)
    assert "parcels_supply" in gdf.columns
    assert "parcels_demand" in gdf.columns
    assert "geometry" in gdf.columns


def test_geometries_are_linestrings():
    gdf = desire_lines(AGENTS, BATCH_SIZES)
    for geom in gdf.geometry:
        assert geom.geom_type == "LineString"


def test_supply_exhausted_to_limiting():
    gdf = desire_lines(AGENTS, BATCH_SIZES)
    # total supply=9, demand=15, limiting=9
    assert gdf["parcels_supply"].sum() == 9


def test_demand_exhausted_to_limiting():
    gdf = desire_lines(AGENTS, BATCH_SIZES)
    assert gdf["parcels_demand"].sum() == 9


def test_supply_equals_demand_per_row():
    gdf = desire_lines(AGENTS, BATCH_SIZES)
    for _, row in gdf.iterrows():
        assert row["parcels_supply"] == row["parcels_demand"]


def test_skips_resource_with_no_supply():
    agents = gpd.GeoDataFrame(
        [{"parcels_supply": 0, "parcels_demand": 6, "geometry": Point(0.5, 0.5)}],
        crs=None,
    )
    gdf = desire_lines(agents, BATCH_SIZES)
    assert len(gdf) == 0


def test_skips_resource_not_in_batch_sizes():
    agents = gpd.GeoDataFrame(
        [
            {"grain_supply": 6, "grain_demand": 0, "geometry": Point(0.25, 0.25)},
            {"grain_supply": 0, "grain_demand": 6, "geometry": Point(0.75, 0.75)},
        ],
        crs=None,
    )
    gdf = desire_lines(agents, BATCH_SIZES)
    assert len(gdf) == 0


def test_empty_when_no_matching_resources():
    agents = gpd.GeoDataFrame(columns=["parcels_supply", "parcels_demand", "geometry"], crs=None)
    gdf = desire_lines(agents, BATCH_SIZES)
    assert len(gdf) == 0
