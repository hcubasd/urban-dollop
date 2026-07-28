import math

from urban_dollop.helpers.log_normal import log_normal
from urban_dollop.helpers.normal import normal_sample
from urban_dollop.helpers.student import t


def vehicle_velocities():
    n_vehicles = math.ceil(log_normal(t(3)))
    n_road_types = math.ceil(log_normal(t(3)))
    vehicles = [f"vehicle_{i + 1}" for i in range(n_vehicles)]
    road_types = [f"road_type_{i + 1}" for i in range(n_road_types)]
    rows = []
    for vehicle in vehicles:
        for road_type in road_types:
            rows.append({
                "vehicle": vehicle,
                "road_type": road_type,
                "velocity": log_normal(normal_sample(0.0, 1.0)),
            })
    return rows
