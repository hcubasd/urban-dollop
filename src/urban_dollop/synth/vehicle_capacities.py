import math

from urban_dollop.helpers.log_normal import log_normal
from urban_dollop.helpers.normal import normal_sample
from urban_dollop.helpers.primes import prime
from urban_dollop.helpers.student import t


def vehicle_capacities():
    n_vehicles = math.ceil(log_normal(t(3)))
    n_resources = math.ceil(log_normal(t(3)))
    vehicles = [f"vehicle_{i + 1}" for i in range(n_vehicles)]
    resources = [f"resource_{i + 1}" for i in range(n_resources)]
    rows = []
    for vehicle in vehicles:
        for resource in resources:
            rows.append({
                "vehicle": vehicle,
                "resource": resource,
                "capacity": prime(math.ceil(log_normal(normal_sample(0.0, 1.0)))),
            })
    return rows
