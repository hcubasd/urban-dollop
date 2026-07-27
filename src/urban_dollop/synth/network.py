import math
import random

import geopandas as gpd
import numpy as np
from scipy.spatial import Delaunay
from shapely.geometry import LineString

from urban_dollop.helpers.log_normal import log_normal
from urban_dollop.helpers.normal import normal_sample
from urban_dollop.helpers.primes import prime
from urban_dollop.helpers.student import t


def network():
    n_points = max(3, prime(math.ceil(log_normal(normal_sample(0.0, 1.0)))))
    points = np.array([(random.uniform(0.0, 1.0), random.uniform(0.0, 1.0)) for _ in range(n_points)])

    n_road_types = math.ceil(log_normal(t(3)))
    road_types = [f"road_type_{i + 1}" for i in range(n_road_types)]
    directions = ["both", "forward", "backward"]

    tri = Delaunay(points)

    edges = set()
    for simplex in tri.simplices:
        for i in range(3):
            a, b = simplex[i], simplex[(i + 1) % 3]
            edges.add((min(a, b), max(a, b)))

    rows = []
    for a, b in edges:
        p1, p2 = points[a], points[b]
        rows.append({
            "grade": normal_sample(0.0, 1.0),
            "road_type": random.choice(road_types),
            "direction": random.choice(directions),
            "geometry": LineString([(float(p1[0]), float(p1[1])), (float(p2[0]), float(p2[1]))]),
        })

    return gpd.GeoDataFrame(rows, crs=None)
