from shapely.geometry import Polygon

from urban_dollop.helpers.sample_point import sample_point

L_SHAPE = Polygon([(0, 0), (2, 0), (2, 1), (1, 1), (1, 2), (0, 2)])


def test_point_always_inside_polygon():
    for _ in range(100):
        assert L_SHAPE.contains(sample_point(L_SHAPE))


def test_point_never_in_the_missing_corner():
    for _ in range(200):
        point = sample_point(L_SHAPE)
        assert not (point.x > 1 and point.y > 1)
