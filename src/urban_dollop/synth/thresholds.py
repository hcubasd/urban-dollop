import math
import random

# Textbook cumulative-logit / proportional-odds cutpoints (McCullagh 1980):
# for a resource with n ordered levels, n-1 thresholds partition a latent
# continuous scale into the n discrete outcomes.


def thresholds(resources):
    """resources: {resource: [level, ...]}, levels distinct within a
    resource (validated here) -- duplicate levels would mean two ordinal
    categories mapping to the identical real-world quantity, which has no
    meaningful interpretation.

    threshold ~ Normal(0, 1), fixed regardless of --sigma, sorted ascending
    per resource: a value being synthesized, not a count. The largest level
    gets threshold=None -- there is no upper cutoff.
    """
    rows = []
    for resource, levels in resources.items():
        if len(levels) != len(set(levels)):
            raise ValueError(f"{resource}: levels must be distinct, got {levels}")
        sorted_levels = sorted(levels)
        mus = sorted(random.normalvariate(0.0, 1.0) for _ in range(len(sorted_levels) - 1))
        for i, level in enumerate(sorted_levels):
            rows.append({
                "resource": resource,
                "resource_level": level,
                "threshold": mus[i] if i < len(mus) else None,
            })
    return rows


def _distinct_levels(n_levels):
    levels = set()
    while len(levels) < n_levels:
        levels.add(math.ceil(math.exp(random.normalvariate(0.0, 1.0))))
    return sorted(levels)


def random_resources(sigma=1.0):
    """Build a full resources dict from scratch. Resource count and each
    resource's level count are both ceil(lognormal(0, sigma)) -- counts,
    the only place --sigma acts. Level values themselves are drawn at fixed
    sigma=1.0 via _distinct_levels, same value/count split as everywhere
    else in this pass."""
    n_resources = math.ceil(math.exp(random.normalvariate(0.0, sigma)))
    resources = {}
    for i in range(n_resources):
        n_levels = math.ceil(math.exp(random.normalvariate(0.0, sigma)))
        resources[f"resource_{i + 1}"] = _distinct_levels(n_levels)
    return resources
