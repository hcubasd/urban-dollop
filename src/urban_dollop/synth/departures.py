import math
import random

from urban_dollop.helpers.log_normal import log_normal
from urban_dollop.helpers.logistic import logistic
from urban_dollop.helpers.normal import normal_sample
from urban_dollop.helpers.primes import prime
from urban_dollop.helpers.student import t


def departures():
    n_resources = math.ceil(log_normal(t(3)))
    interval_counts = [prime(math.ceil(log_normal(normal_sample(0.0, 1.0)))) for _ in range(n_resources)]
    max_intervals = max(interval_counts)
    full_intervals = list(range(1, max_intervals + 1))

    rows = []
    for i, n_intervals in enumerate(interval_counts):
        resource = f"resource_{i + 1}"
        intervals = sorted(random.sample(full_intervals, n_intervals))
        beta = normal_sample(0.0, 1.0)
        mus = sorted(normal_sample(0.0, 1.0) for _ in range(n_intervals - 1))
        cum_probs = [0.0] + [logistic(mu - beta) for mu in mus] + [1.0]
        for k, interval in enumerate(intervals):
            rows.append({
                "resource": resource,
                "time_interval": interval,
                "probability": cum_probs[k + 1] - cum_probs[k],
            })

    return rows
