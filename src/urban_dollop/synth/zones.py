import math
import random

import geopandas as gpd
import numpy as np
from scipy.spatial import Voronoi
from shapely.geometry import Polygon
from shapely.ops import unary_union

from urban_dollop.helpers.log_normal import log_normal
from urban_dollop.helpers.normal import normal_sample
from urban_dollop.helpers.primes import prime


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


def zones():
    n_zones = prime(math.ceil(log_normal(normal_sample(0.0, 1.0))))
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
    labels = [f"value_{i + 1}" for i in range(n_zones)]
    return gpd.GeoDataFrame({"stratum_1": labels, "geometry": geometries}, crs=None)
