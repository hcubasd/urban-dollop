import geopandas as gpd

from urban_dollop.synth.network import network


def test_returns_geodataframe():
    gdf = network()
    assert isinstance(gdf, gpd.GeoDataFrame)


def test_has_required_columns():
    gdf = network()
    assert "link_id" in gdf.columns
    assert "grade" in gdf.columns
    assert "road_type" in gdf.columns
    assert "direction" in gdf.columns
    assert "geometry" in gdf.columns


def test_geometries_are_linestrings():
    gdf = network()
    for geom in gdf.geometry:
        assert geom.geom_type == "LineString"


def test_no_degenerate_edges():
    gdf = network()
    for geom in gdf.geometry:
        assert geom.length > 0


def test_directions_are_valid():
    gdf = network()
    valid = {"both", "forward", "backward"}
    assert set(gdf["direction"].unique()).issubset(valid)


def test_road_types_are_sequential():
    gdf = network()
    for rt in gdf["road_type"]:
        assert rt.startswith("road_type_")


def test_grade_is_float():
    gdf = network()
    for g in gdf["grade"]:
        assert isinstance(g, float)


def test_link_ids_are_unique():
    gdf = network()
    assert gdf["link_id"].nunique() == len(gdf)


def test_crs_is_none():
    gdf = network()
    assert gdf.crs is None
