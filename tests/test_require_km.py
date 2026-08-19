import geopandas as gpd
import pytest
from shapely.geometry import LineString

from urban_dollop.helpers.require_km import require_km


def test_rejects_a_missing_crs():
    gdf = gpd.GeoDataFrame({"geometry": [LineString([(0, 0), (1000, 0)])]})
    with pytest.raises(ValueError):
        require_km(gdf, "network.gpkg")


def test_scales_a_projected_metre_crs_exactly():
    # RD New -- a real, metre-based projected CRS.
    gdf = gpd.GeoDataFrame({"geometry": [LineString([(0, 0), (1000, 0)])]}, crs="EPSG:28992")
    km = require_km(gdf, "network.gpkg")
    assert km.geometry.length[0] == pytest.approx(1.0)


def test_scales_a_projected_foot_crs_by_its_own_factor():
    # EPSG:2913 -- Oregon North, US survey feet. 3280.8333 ft is ~1 km,
    # so this is checking the conversion actually reads the CRS's own
    # factor rather than assuming metres everywhere.
    gdf = gpd.GeoDataFrame({"geometry": [LineString([(0, 0), (3280.8333, 0)])]}, crs="EPSG:2913")
    km = require_km(gdf, "network.gpkg")
    assert km.geometry.length[0] == pytest.approx(1.0, rel=1e-3)


def test_reprojects_a_geographic_crs_before_scaling():
    # Two points a real ~1km apart near Amsterdam, in WGS84 lat/lon --
    # there is no fixed degrees-to-km factor, so this only comes out
    # right if it actually reprojects first.
    gdf = gpd.GeoDataFrame(
        {"geometry": [LineString([(4.9, 52.37), (4.9145, 52.37)])]}, crs="EPSG:4326",
    )
    km = require_km(gdf, "network.gpkg")
    assert km.geometry.length[0] == pytest.approx(1.0, rel=0.05)


def test_result_carries_its_own_valid_crs():
    gdf = gpd.GeoDataFrame({"geometry": [LineString([(0, 0), (1000, 0)])]}, crs="EPSG:28992")
    km = require_km(gdf, "network.gpkg")
    assert km.crs is not None


def test_does_not_mutate_the_input():
    gdf = gpd.GeoDataFrame({"geometry": [LineString([(0, 0), (1000, 0)])]}, crs="EPSG:28992")
    require_km(gdf, "network.gpkg")
    assert gdf.geometry.length[0] == 1000.0
