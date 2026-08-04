import random

from urban_dollop.helpers.random_count import random_count


def time_intervals(sigma=1.0):
    """One row per synthesized time interval: a sequential label
    (interval_1, interval_2, ...) and a duration. random_count(sigma) is
    the only place --sigma acts, for the interval count -- duration is a
    value, not a count, and its distribution is deliberately unassuming
    (lognormvariate(0.0, 1.0), fixed regardless of sigma), since the
    simulation period and interval units (an hour, a day, a month) are
    entirely up to whoever uses this data -- there's no canonical shape
    to preserve or invent around.

    Row order is not incidental: network_loads treats file order as
    chronological order, walking intervals in the order they appear
    rather than parsing the label -- so rows are always emitted
    interval_1, interval_2, ... in that order, never shuffled.
    """
    return [
        {"time_interval": f"interval_{i + 1}", "duration": random.lognormvariate(0.0, 1.0)}
        for i in range(random_count(sigma))
    ]
