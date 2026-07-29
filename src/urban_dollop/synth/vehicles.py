import math
import random

from urban_dollop.helpers.log_normal import log_normal
from urban_dollop.helpers.normal import normal_sample
from urban_dollop.helpers.student import t


def vehicles():
    n_vehicles = math.ceil(log_normal(t(3)))
    n_vehicle_types = math.ceil(log_normal(t(3)))
    vehicle_types = [f"vehicle_type_{i + 1}" for i in range(n_vehicle_types)]
    rows = []
    for i in range(n_vehicles):
        rows.append({
            "vehicle": f"vehicle_{i + 1}",
            "vehicle_type": random.choice(vehicle_types),
            "bpr_alpha": log_normal(normal_sample(0.0, 1.0)),
            "bpr_beta": log_normal(normal_sample(0.0, 1.0)),
            "time_cost": normal_sample(0.0, 1.0),
            "distance_cost": normal_sample(0.0, 1.0),
            "pcu": log_normal(normal_sample(0.0, 1.0)),
        })
    return rows
