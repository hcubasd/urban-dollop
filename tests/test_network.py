import pytest

from urban_dollop.synth.network import _edges, network


def test_edges_empty_for_zero_or_one_point():
    assert _edges([]) == []
    assert _edges([(0.0, 0.0)]) == []


def test_edges_direct_connection_for_two_points():
    assert _edges([(0.0, 0.0), (1.0, 1.0)]) == [(0, 1)]


def test_edges_triangulates_three_non_collinear_points():
    edges = _edges([(0.0, 0.0), (1.0, 0.0), (0.0, 1.0)])
    assert set(edges) == {(0, 1), (0, 2), (1, 2)}


def test_zero_sigma_is_a_single_point_no_edges():
    gdf = network(sigma=0.0)
    assert len(gdf) == 0
    assert list(gdf.columns) == ["link_id", "grade", "road_type", "oneway", "geometry"]


def test_oneway_edges_have_a_definite_direction():
    for _ in range(50):
        gdf = network(sigma=2.0)
        for _, row in gdf.iterrows():
            if row["oneway"]:
                coords = list(row["geometry"].coords)
                assert coords[0] != coords[1]


def test_grade_bounds_hold_across_many_draws():
    gdf = network(sigma=2.0)
    assert all(-6.0 <= g <= 6.0 for g in gdf["grade"])


def test_link_ids_are_unique():
    gdf = network(sigma=2.0)
    assert gdf["link_id"].tolist() == list(range(len(gdf)))


def test_road_type_vocabulary_is_labeled_sequentially():
    gdf = network(sigma=2.0)
    for road_type in gdf["road_type"]:
        assert road_type.startswith("road_type_")


def test_given_geometries_used_as_is_and_ignore_sigma_for_count():
    from shapely.geometry import LineString

    geometries = [LineString([(0.0, 0.0), (1.0, 1.0)]), LineString([(1.0, 1.0), (2.0, 0.0)])]
    gdf = network(geometries=geometries, sigma=5.0, crs="EPSG:4326")
    assert len(gdf) == 2
    assert list(gdf["geometry"]) == geometries
    assert gdf["link_id"].tolist() == [0, 1]
    assert gdf.crs == "EPSG:4326"


def test_given_geometries_requires_crs():
    from shapely.geometry import LineString

    geometries = [LineString([(0.0, 0.0), (1.0, 1.0)])]
    with pytest.raises(ValueError):
        network(geometries=geometries, sigma=1.0)


def test_invented_geometry_gets_a_real_crs():
    gdf = network(sigma=2.0)
    assert gdf.crs is not None
