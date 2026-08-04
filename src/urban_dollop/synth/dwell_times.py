import random

from urban_dollop.helpers.random_count import random_count


def dwell_times(resources=None, sigma=1.0):
    """One row per resource: dwell_time (how long a vehicle dwells before
    its return trip) and load_pct (the fraction of load carried back).
    resources=None means nothing exists yet -- invent both the count
    (random_count(sigma), the only place --sigma acts) and the labels
    (resource_1, resource_2, ...). resources given means the shape is
    already decided -- values get synthesized for exactly those
    resources, ignoring sigma for the count.

    dwell_time and load_pct are both values, not counts, and stay fixed
    regardless of sigma: dwell_time gets the same deliberately unassuming
    lognormvariate(0.0, 1.0) treatment as time_intervals' duration (a
    positive time span with no canonical shape to preserve), and load_pct
    is already the canonical choice for "a fraction in [0, 1)" as plain
    random.random(), nothing legacy to migrate there.
    """
    if resources is None:
        resources = [f"resource_{i + 1}" for i in range(random_count(sigma))]
    return [
        {"resource": resource, "dwell_time": random.lognormvariate(0.0, 1.0), "load_pct": random.random()}
        for resource in resources
    ]
