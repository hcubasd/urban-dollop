import math

from urban_dollop.helpers.log_normal import log_normal
from urban_dollop.helpers.normal import normal_sample
from urban_dollop.helpers.student import t


def alternative_specific_constants():
    n_resources = math.ceil(log_normal(t(3)))
    n_vehicles = math.ceil(log_normal(t(3)))
    resources = [f"resource_{i + 1}" for i in range(n_resources)]
    vehicles = [f"vehicle_{i + 1}" for i in range(n_vehicles)]
    rows = []
    for resource in resources:
        for vehicle in vehicles:
            rows.append({
                "resource": resource,
                "vehicle": vehicle,
                "alpha": normal_sample(0.0, 1.0),
            })
    return rows
