import random

from shapely.geometry import Point


def sample_point(polygon):
    """A uniformly-random point inside `polygon`: draw x, y uniform over
    its bounding box, rejecting and redrawing until the point actually
    falls inside the polygon, not just its (generally larger) box.
    """
    minx, miny, maxx, maxy = polygon.bounds
    while True:
        point = Point(random.uniform(minx, maxx), random.uniform(miny, maxy))
        if polygon.contains(point):
            return point
