import math
import random

from urban_dollop.helpers.log_normal import log_normal
from urban_dollop.helpers.normal import normal_sample
from urban_dollop.helpers.student import t

GRADIENT_BINS = [-6, -4, -2, 0, 2, 4, 6]
PAYLOAD_BINS = [0, 50, 100]


def copert_v_coefficients():
    n_vehicle_types = math.ceil(log_normal(t(3)))
    n_pollutants = math.ceil(log_normal(t(3)))
    pollutants = [f"pollutant_{i + 1}" for i in range(n_pollutants)]
    rows = []
    for i in range(n_vehicle_types):
        vehicle_type = f"vehicle_type_{i + 1}"
        for pollutant in pollutants:
            for gradient_bin in GRADIENT_BINS:
                for payload_bin in PAYLOAD_BINS:
                    rows.append({
                        "vehicle_type": vehicle_type,
                        "pollutant": pollutant,
                        "gradient_bin": gradient_bin,
                        "payload_bin": payload_bin,
                        "alpha": normal_sample(0.0, 1.0),
                        "beta": normal_sample(0.0, 1.0),
                        "gamma": normal_sample(0.0, 1.0),
                        "delta": normal_sample(0.0, 1.0),
                        "epsilon": normal_sample(0.0, 1.0),
                        "zeta": normal_sample(0.0, 1.0),
                        "eta": normal_sample(0.0, 1.0),
                        "rf": random.random(),
                    })
    return rows
