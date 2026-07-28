import math

from urban_dollop.helpers.log_normal import log_normal
from urban_dollop.helpers.normal import normal_sample
from urban_dollop.helpers.primes import prime


def time_intervals():
    n_intervals = prime(math.ceil(log_normal(normal_sample(0.0, 1.0))))
    rows = []
    for i in range(n_intervals):
        rows.append({
            "time_interval": f"interval_{i + 1}",
            "duration": log_normal(normal_sample(0.0, 1.0)),
        })
    return rows
