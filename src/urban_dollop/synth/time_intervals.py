import random

from urban_dollop.helpers.random_count import random_count


def time_intervals(labels=None, sigma=1.0):
    """One row per time interval: a label and a duration. labels=None
    means nothing exists yet -- invent both the count (random_count(sigma),
    the only place --sigma acts) and the labels (interval_1, interval_2,
    ...). labels given means the shape is already decided -- durations get
    synthesized for exactly those labels, in that order, ignoring sigma
    for the count.

    duration is a value, not a count, and its distribution is deliberately
    unassuming (lognormvariate(0.0, 1.0), fixed regardless of sigma),
    since the simulation period and interval units (an hour, a day, a
    month) are entirely up to whoever uses this data -- there's no
    canonical shape to preserve or invent around.

    Row order is not incidental: network_loads treats file order as
    chronological order, walking intervals in the order they appear
    rather than parsing the label -- so given labels are used in the
    order they're given, and invented labels are always emitted
    interval_1, interval_2, ... in that order, never shuffled.
    """
    if labels is None:
        labels = [f"interval_{i + 1}" for i in range(random_count(sigma))]
    return [{"time_interval": label, "duration": random.lognormvariate(0.0, 1.0)} for label in labels]
