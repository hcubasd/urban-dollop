import random

import geopandas as gpd
import numpy as np
from scipy.spatial import Delaunay
from shapely.geometry import LineString

from urban_dollop.helpers.random_count import random_count

_COLUMNS = ["link_id", "grade", "road_type", "oneway", "geometry"]


def _edges(points):
    """Unordered (i, j) point-index pairs to connect. Delaunay needs at
    least 3 non-degenerate points, so the two smaller cases are handled
    directly: one point has nothing to connect to, two points are just
    connected to each other.
    """
    n = len(points)
    if n < 2:
        return []
    if n == 2:
        return [(0, 1)]
    tri = Delaunay(np.array(points))
    edge_set = set()
    for simplex in tri.simplices:
        for i in range(3):
            a, b = simplex[i], simplex[(i + 1) % 3]
            edge_set.add((min(a, b), max(a, b)))
    return sorted(edge_set)


def network(sigma=1.0):
    """A GeoDataFrame of road links over the unit square: scatter points,
    connect them (Delaunay triangulation once there are enough points to
    triangulate), and label each edge. random_count(sigma) is the only
    place --sigma acts, for both the point count and the road_type
    vocabulary size -- everything else here is a value, not a count, and
    stays fixed regardless of sigma.

    Direction is a plain boolean, not a three-way flag: 'oneway' true
    means travel is only legal start-to-end as stored, so start/end are
    chosen (a coin flip) to already match the allowed direction, rather
    than storing an arbitrary order plus a correction flag (the footgun
    OSM's oneway=-1 exists to patch). 'oneway' false means both
    directions are legal and order is immaterial. grade is always
    relative to whichever order ends up stored -- the reverse direction
    is just its negation, not an independent draw.
    """
    n_points = random_count(sigma)
    points = [(random.uniform(0.0, 1.0), random.uniform(0.0, 1.0)) for _ in range(n_points)]

    n_road_types = random_count(sigma)
    road_types = [f"road_type_{i + 1}" for i in range(n_road_types)]

    rows = []
    for i, (a, b) in enumerate(_edges(points)):
        oneway = random.random() < 0.5
        if oneway and random.random() < 0.5:
            a, b = b, a
        rows.append({
            "link_id": i,
            "grade": random.triangular(-6.0, 6.0, 0.0),
            "road_type": random.choice(road_types),
            "oneway": oneway,
            "geometry": LineString([points[a], points[b]]),
        })

    if not rows:
        return gpd.GeoDataFrame(columns=_COLUMNS, crs=None)
    return gpd.GeoDataFrame(rows, crs=None)
