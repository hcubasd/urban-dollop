import random

from urban_dollop.helpers.random_count import random_count


def dwell_times(sigma=1.0):
    """One row per synthesized resource: dwell_time (how long a vehicle
    dwells before its return trip) and load_pct (the fraction of load
    carried back). Self-contained -- invents its own resources.

    random_count(sigma) is the only place --sigma acts, for the resource
    count. dwell_time and load_pct are both values, not counts, and stay
    fixed regardless of sigma: dwell_time gets the same deliberately
    unassuming lognormvariate(0.0, 1.0) treatment as time_intervals'
    duration (a positive time span with no canonical shape to preserve),
    and load_pct is already the canonical choice for "a fraction in
    [0, 1)" as plain random.random(), nothing legacy to migrate there.
    """
    return [
        {
            "resource": f"resource_{i + 1}",
            "dwell_time": random.lognormvariate(0.0, 1.0),
            "load_pct": random.random(),
        }
        for i in range(random_count(sigma))
    ]
