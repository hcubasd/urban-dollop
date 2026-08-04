import geopandas as gpd
import pytest
from shapely.geometry import LineString

from urban_dollop.cli.synth_network import read_network, network_need_synthesis


def test_read_network_none_if_absent(tmp_path):
    assert read_network(str(tmp_path / "missing.gpkg")) is None


def test_read_network_shape_only(tmp_path):
    path = tmp_path / "network.gpkg"
    geoms = [LineString([(0.0, 0.0), (1.0, 1.0)]), LineString([(1.0, 1.0), (2.0, 0.0)])]
    gpd.GeoDataFrame({
        "grade": [None, None],
        "road_type": [None, None],
        "oneway": [None, None],
        "geometry": geoms,
    }).to_file(str(path), driver="GPKG")
    geometries, complete = read_network(str(path))
    assert len(geometries) == 2
    assert complete is False


def test_read_network_complete(tmp_path):
    path = tmp_path / "network.gpkg"
    geoms = [LineString([(0.0, 0.0), (1.0, 1.0)])]
    gpd.GeoDataFrame({
        "grade": [1.5],
        "road_type": ["road_type_1"],
        "oneway": [True],
        "geometry": geoms,
    }).to_file(str(path), driver="GPKG")
    geometries, complete = read_network(str(path))
    assert complete is True


def test_read_network_missing_column_rejected(tmp_path):
    path = tmp_path / "bad.gpkg"
    gpd.GeoDataFrame({"geometry": [LineString([(0.0, 0.0), (1.0, 1.0)])]}).to_file(str(path), driver="GPKG")
    with pytest.raises(ValueError):
        read_network(str(path))


def test_read_network_missing_geometry_rejected(tmp_path):
    path = tmp_path / "bad.gpkg"
    gpd.GeoDataFrame({
        "grade": [None],
        "road_type": [None],
        "oneway": [None],
        "geometry": [None],
    }).to_file(str(path), driver="GPKG")
    with pytest.raises(ValueError):
        read_network(str(path))


def test_read_network_mixed_attributes_rejected(tmp_path):
    path = tmp_path / "bad.gpkg"
    gpd.GeoDataFrame({
        "grade": [1.5, None],
        "road_type": [None, None],
        "oneway": [None, None],
        "geometry": [LineString([(0.0, 0.0), (1.0, 1.0)]), LineString([(1.0, 1.0), (2.0, 0.0)])],
    }).to_file(str(path), driver="GPKG")
    with pytest.raises(ValueError):
        read_network(str(path))


def test_network_need_synthesis_true_when_absent():
    assert network_need_synthesis(None) is True


def test_network_need_synthesis_true_when_shape_only():
    assert network_need_synthesis(([1], False)) is True


def test_network_need_synthesis_false_when_complete():
    assert network_need_synthesis(([1], True)) is False
