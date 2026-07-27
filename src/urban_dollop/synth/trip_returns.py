import math
import random

from urban_dollop.helpers.log_normal import log_normal
from urban_dollop.helpers.normal import normal_sample
from urban_dollop.helpers.primes import prime
from urban_dollop.helpers.student import t


def trip_returns():
    n_resources = math.ceil(log_normal(t(3)))
    rows = []
    for i in range(n_resources):
        rows.append({
            "resource": f"resource_{i + 1}",
            "dwell_time": prime(math.ceil(log_normal(normal_sample(0.0, 1.0)))),
            "load_pct": random.random(),
        })
    return rows
