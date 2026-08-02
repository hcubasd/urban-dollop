from urban_dollop.helpers.distinct_values import distinct_values
from urban_dollop.helpers.random_count import random_count


def random_resources(sigma):
    """Invent a full resource/resource_level shape from scratch: resource
    count and each resource's level count are both random_count(sigma).
    Level values also use sigma -- see distinct_values for why that's
    correct despite resource_level playing effect/threshold's "value" role
    in some respects. Returns rows with threshold=None, ready to be filled.
    """
    n_resources = random_count(sigma)
    rows = []
    for i in range(n_resources):
        n_levels = random_count(sigma)
        for level in distinct_values(n_levels, sigma):
            rows.append({"resource": f"resource_{i + 1}", "resource_level": level, "threshold": None})
    return rows
