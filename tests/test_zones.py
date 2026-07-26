import geopandas as gpd
import pytest
from shapely.geometry import Polygon

from urban_dollop.synth.zones import zones


BOX = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])


def test_returns_geodataframe():
    gdf = zones()
    assert isinstance(gdf, gpd.GeoDataFrame)


def test_has_stratum_and_geometry_columns():
    gdf = zones()
    assert "stratum_1" in gdf.columns
    assert "geometry" in gdf.columns


def test_stratum_values_are_sequential():
    gdf = zones()
    n = len(gdf)
    assert list(gdf["stratum_1"]) == [f"value_{i + 1}" for i in range(n)]


def test_all_geometries_are_valid_polygons():
    gdf = zones()
    for geom in gdf.geometry:
        assert geom is not None
        assert geom.is_valid
        assert geom.geom_type in ("Polygon", "MultiPolygon")


def test_all_geometries_within_unit_square():
    gdf = zones()
    for geom in gdf.geometry:
        assert BOX.contains(geom) or BOX.equals(geom)


def test_crs_is_none():
    gdf = zones()
    assert gdf.crs is None


def test_zones_tile_unit_square():
    gdf = zones()
    union = gdf.geometry.union_all()
    assert abs(union.area - 1.0) < 1e-6
