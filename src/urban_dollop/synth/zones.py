import random

import geopandas as gpd
import numpy as np
from scipy.spatial import Voronoi
from shapely.geometry import Polygon

from urban_dollop.helpers.random_count import random_count


def _clip_voronoi_cell(vor, region_index, bounds):
    box = Polygon([
        (bounds[0], bounds[1]),
        (bounds[2], bounds[1]),
        (bounds[2], bounds[3]),
        (bounds[0], bounds[3]),
    ])
    region = vor.regions[region_index]
    if -1 in region or len(region) == 0:
        return None
    poly = Polygon([vor.vertices[i] for i in region])
    return poly.intersection(box)


def zones(zone_ids=None, sigma=1.0):
    """A GeoDataFrame of Voronoi-tessellated zone polygons over the unit
    square, one row per zone_id. zone_ids=None means nothing exists yet --
    invent both the count (random_count(sigma), the only place --sigma
    acts) and the labels (plain integers 1, 2, ... matching effects.csv's
    zone_id convention). zone_ids given means the shape is already decided
    -- geometry gets synthesized for exactly those zone_ids, in that
    order, ignoring sigma for the count (there's nothing left for it to
    control).
    """
    if zone_ids is None:
        zone_ids = list(range(1, random_count(sigma) + 1))
    n_zones = len(zone_ids)

    # seed points inside [0.1, 0.9]^2 so boundary cells are well-formed
    points = [(random.uniform(0.1, 0.9), random.uniform(0.1, 0.9)) for _ in range(n_zones)]
    # mirror points around all four edges to bound infinite regions
    mirrored = []
    for x, y in points:
        mirrored += [(x, -y), (x, 2 - y), (-x, y), (2 - x, y)]
    all_points = np.array(points + mirrored)
    vor = Voronoi(all_points)
    bounds = (0.0, 0.0, 1.0, 1.0)
    geometries = []
    for i in range(n_zones):
        point_region = vor.point_region[i]
        geom = _clip_voronoi_cell(vor, point_region, bounds)
        geometries.append(geom)
    # From-scratch invention: no real file to inherit a CRS from.
    return gpd.GeoDataFrame({"zone_id": zone_ids, "geometry": geometries}, crs='EPSG:3857')
