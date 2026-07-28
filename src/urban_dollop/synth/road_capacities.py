import math

from urban_dollop.helpers.log_normal import log_normal
from urban_dollop.helpers.normal import normal_sample
from urban_dollop.helpers.student import t


def road_capacities():
    n_road_types = math.ceil(log_normal(t(3)))
    rows = []
    for i in range(n_road_types):
        rows.append({
            "road_type": f"road_type_{i + 1}",
            "capacity": log_normal(normal_sample(0.0, 1.0)),
        })
    return rows
