import math
import random

from urban_dollop.helpers.log_normal import log_normal
from urban_dollop.helpers.normal import normal_sample
from urban_dollop.helpers.primes import prime, primes
from urban_dollop.helpers.student import t


def resource_thresholds():
    n_resources = math.ceil(log_normal(t(3)))
    level_counts = [prime(math.ceil(log_normal(normal_sample(0.0, 1.0)))) for _ in range(n_resources)]
    max_levels = max(level_counts)
    headers = primes(max_levels)

    rows = []
    for i, n_levels in enumerate(level_counts):
        mus = sorted(normal_sample(0.0, 1.0) for _ in range(n_levels - 1))
        positions = sorted(random.sample(range(max_levels - 1), n_levels - 1))
        row = {"resource": f"resource_{i + 1}"}
        for h in headers:
            row[h] = None
        for pos, mu in zip(positions, mus):
            row[headers[pos]] = mu
        rows.append(row)

    return headers, rows
