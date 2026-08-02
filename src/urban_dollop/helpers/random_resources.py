from urban_dollop.helpers.distinct_values import distinct_values
from urban_dollop.helpers.random_count import random_count


def random_resources(sigma):
    """Invent a full resource/resource_level shape from scratch: resource
    count and each resource's level count are both random_count(sigma) --
    counts, the only place --sigma acts. Level values themselves come from
    distinct_values, fixed at sigma=1.0 always, since they're values, not
    counts. Returns rows with threshold=None, ready to be filled.
    """
    n_resources = random_count(sigma)
    rows = []
    for i in range(n_resources):
        n_levels = random_count(sigma)
        for level in distinct_values(n_levels):
            rows.append({"resource": f"resource_{i + 1}", "resource_level": level, "threshold": None})
    return rows
