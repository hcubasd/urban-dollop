import math

from urban_dollop.helpers.log_normal import log_normal
from urban_dollop.helpers.normal import normal_sample
from urban_dollop.helpers.student import t


def emission_factors():
    n_vehicle_types = math.ceil(log_normal(t(3)))
    n_pollutants = math.ceil(log_normal(t(3)))
    pollutants = [f"pollutant_{i + 1}" for i in range(n_pollutants)]
    rows = []
    for i in range(n_vehicle_types):
        for pollutant in pollutants:
            rows.append({
                "vehicle_type": f"vehicle_type_{i + 1}",
                "pollutant": pollutant,
                "ef": log_normal(normal_sample(0.0, 1.0)),
            })
    return rows
