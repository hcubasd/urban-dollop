import geopandas as gpd
import pytest
from shapely.geometry import Point

from urban_dollop.cli.synth_zones import read_zones, zones_need_synthesis


def test_read_zones_none_if_absent(tmp_path):
    assert read_zones(str(tmp_path / "missing.gpkg")) is None


def test_read_zones_shape_only(tmp_path):
    path = tmp_path / "zones.gpkg"
    gpd.GeoDataFrame({"zone_id": [1, 2, 3], "geometry": [None, None, None]}, crs="EPSG:4326").to_file(str(path), driver="GPKG")
    zone_ids, complete = read_zones(str(path))
    assert zone_ids == [1, 2, 3]
    assert complete is False


def test_read_zones_complete(tmp_path):
    path = tmp_path / "zones.gpkg"
    gpd.GeoDataFrame({
        "zone_id": [1, 2],
        "geometry": [Point(0, 0), Point(1, 1)],
    }, crs="EPSG:4326").to_file(str(path), driver="GPKG")
    zone_ids, complete = read_zones(str(path))
    assert zone_ids == [1, 2]
    assert complete is True


def test_read_zones_missing_crs_rejected(tmp_path):
    path = tmp_path / "bad.gpkg"
    gpd.GeoDataFrame({"zone_id": [1], "geometry": [Point(0, 0)]}).to_file(str(path), driver="GPKG")
    with pytest.raises(ValueError):
        read_zones(str(path))


def test_read_zones_missing_column_rejected(tmp_path):
    path = tmp_path / "bad.gpkg"
    gpd.GeoDataFrame({"geometry": [None]}, crs="EPSG:4326").to_file(str(path), driver="GPKG")
    with pytest.raises(ValueError):
        read_zones(str(path))


def test_read_zones_duplicate_ids_rejected(tmp_path):
    path = tmp_path / "bad.gpkg"
    gpd.GeoDataFrame({"zone_id": [1, 1], "geometry": [None, None]}, crs="EPSG:4326").to_file(str(path), driver="GPKG")
    with pytest.raises(ValueError):
        read_zones(str(path))


def test_read_zones_mixed_geometry_rejected(tmp_path):
    path = tmp_path / "bad.gpkg"
    gpd.GeoDataFrame({
        "zone_id": [1, 2],
        "geometry": [Point(0, 0), None],
    }, crs="EPSG:4326").to_file(str(path), driver="GPKG")
    with pytest.raises(ValueError):
        read_zones(str(path))


def test_zones_need_synthesis_true_when_absent():
    assert zones_need_synthesis(None) is True


def test_zones_need_synthesis_true_when_shape_only():
    assert zones_need_synthesis(([1, 2], False)) is True


def test_zones_need_synthesis_false_when_complete():
    assert zones_need_synthesis(([1, 2], True)) is False
