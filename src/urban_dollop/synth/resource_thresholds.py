import math
import random

from urban_dollop.helpers.log_normal import log_normal
from urban_dollop.helpers.normal import normal_sample
from urban_dollop.helpers.primes import prime, primes
from urban_dollop.helpers.student import t


def resource_thresholds():
    n_resources = math.ceil(log_normal(t(3)))
    level_counts = [prime(math.ceil(log_normal(normal_sample(0.0, 1.0)))) for _ in range(n_resources)]
    full_primes = primes(max(level_counts))

    rows = []
    for i, n_levels in enumerate(level_counts):
        resource = f"resource_{i + 1}"
        levels = sorted(random.sample(full_primes, n_levels))
        mus = sorted(normal_sample(0.0, 1.0) for _ in range(n_levels - 1))
        for j, level in enumerate(levels):
            rows.append({
                "resource": resource,
                "resource_level": level,
                "threshold": mus[j] if j < len(mus) else None,
            })

    return rows
