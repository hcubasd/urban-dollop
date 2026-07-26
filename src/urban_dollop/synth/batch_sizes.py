import math
import random

from urban_dollop.helpers.log_normal import log_normal
from urban_dollop.helpers.logistic import logistic
from urban_dollop.helpers.normal import normal_sample
from urban_dollop.helpers.primes import prime, primes
from urban_dollop.helpers.student import t


def batch_sizes():
    n_resources = math.ceil(log_normal(t(3)))
    level_counts = [prime(math.ceil(log_normal(normal_sample(0.0, 1.0)))) for _ in range(n_resources)]
    full_primes = primes(max(level_counts))

    columns = {}
    for i, n_levels in enumerate(level_counts):
        resource = f"resource_{i + 1}"
        levels = sorted(random.sample(full_primes, n_levels))
        beta = normal_sample(0.0, 1.0)
        mus = sorted(normal_sample(0.0, 1.0) for _ in range(n_levels - 1))
        cum_probs = [0.0] + [logistic(mu - beta) for mu in mus] + [1.0]
        probs = {level: cum_probs[k + 1] - cum_probs[k] for k, level in enumerate(levels)}
        columns[resource] = {p: probs.get(p, 0.0) for p in full_primes}

    return full_primes, columns
