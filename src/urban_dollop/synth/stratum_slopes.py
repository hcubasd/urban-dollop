import itertools
import math

from urban_dollop.helpers.log_normal import log_normal
from urban_dollop.helpers.normal import normal_sample
from urban_dollop.helpers.primes import prime
from urban_dollop.helpers.student import t


def stratum_slopes():
    n_dims = min(math.ceil(log_normal(t(3))), 4)
    dim_values = [
        [f"zone_{j + 1}" for j in range(min(prime(math.ceil(log_normal(normal_sample(0.0, 1.0)))), 7))],
        *[
            [f"value_{j + 1}" for j in range(min(prime(math.ceil(log_normal(normal_sample(0.0, 1.0)))), 7))]
            for _ in range(n_dims - 1)
        ],
    ]
    dim_names = ["zone_id"] + [f"stratum_{i + 1}" for i in range(n_dims - 1)]

    rows = []
    for combo in itertools.product(*dim_values):
        row = dict(zip(dim_names, combo))
        row["slope"] = normal_sample(0.0, 1.0)
        rows.append(row)

    return rows
