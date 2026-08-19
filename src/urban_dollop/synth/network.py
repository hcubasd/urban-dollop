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


def network(geometries=None, sigma=1.0, crs=None):
    """A GeoDataFrame of road links: link_id, grade, road_type, oneway,
    and a 2-point LineString. geometries=None means nothing exists yet --
    invent both the topology (points scattered over the unit square,
    connected by Delaunay triangulation once there are enough to
    triangulate -- below that, the two smaller cases in _edges are
    handled directly) and the attributes -- and the output carries a
    fixed EPSG:3857, since there is no real file to inherit a CRS from.
    geometries given means the shape is already decided -- attributes
    get synthesized for exactly that geometry, in that order, ignoring
    sigma for the point/edge count (there's nothing left for it to
    control) -- and crs is then required, the caller's own file's real
    CRS carried straight through rather than replaced: this geometry
    wasn't invented here, so it isn't this function's CRS to assign.

    random_count(sigma) is the only place --sigma acts, for the point
    count (invented-geometry case only) and the road_type vocabulary
    size (both cases); everything else is a value, not a count, and
    stays fixed regardless of sigma.

    oneway is a plain boolean rather than a three-way flag. In the
    invented-geometry case, a LineString's start and end are just two
    points with no inherent direction of travel, so when a link is
    one-way the start/end order is chosen (a coin flip) to already match
    the allowed direction, rather than storing an arbitrary order
    alongside a flag saying whether to walk it backward -- the same
    footgun OSM's oneway=-1 tag exists to patch, avoided here by
    controlling construction instead of correcting it after the fact.
    That trick has no equivalent when geometry is given rather than
    invented: real geometry's coordinate order is whatever it already
    is, so a one-way link there is just as likely to have been "walked
    backward" as not -- an unavoidable property of not having authored
    the geometry ourselves, not a gap in this logic. Either way, when
    oneway is false both directions are legal and order is immaterial,
    and grade is always relative to whichever order the geometry stores
    -- the reverse direction is its negation, not an independent draw.
    """
    n_road_types = random_count(sigma)
    road_types = [f"road_type_{i + 1}" for i in range(n_road_types)]

    rows = []
    if geometries is None:
        crs = 'EPSG:3857'
        n_points = random_count(sigma)
        points = [(random.uniform(0.0, 1.0), random.uniform(0.0, 1.0)) for _ in range(n_points)]
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
    else:
        if crs is None:
            raise ValueError("network(): crs is required when geometries is given -- see docstring")
        for i, geometry in enumerate(geometries):
            rows.append({
                "link_id": i,
                "grade": random.triangular(-6.0, 6.0, 0.0),
                "road_type": random.choice(road_types),
                "oneway": random.random() < 0.5,
                "geometry": geometry,
            })

    if not rows:
        return gpd.GeoDataFrame(columns=_COLUMNS, crs=crs)
    return gpd.GeoDataFrame(rows, crs=crs)
