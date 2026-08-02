from urban_dollop.helpers.random_level import random_level


def distinct_values(n, sigma):
    """n distinct non-negative integers, sorted, each candidate drawn via
    random_level (ceil(lognormal(0, sigma)) - 1, zero-inclusive -- a
    resource_level can legitimately be zero, unlike a plain count). Unlike
    a terminal output value (effect, threshold), this plays stratum_value's
    shape-defining role -- it just has real random content instead of a
    deterministic label -- so it uses the same sigma that determined n,
    rather than a fixed one: as n grows (itself driven by sigma), the value
    space it's drawn from widens too, keeping n distinct values reachable
    instead of forcing a rejection-sampling loop against a fixed,
    tightly-clustered distribution. Duplicates are re-drawn: two ordinal
    levels sharing a value would mean two categories mapping to the
    identical real-world quantity, which has no meaningful interpretation.
    """
    values = set()
    while len(values) < n:
        values.add(random_level(sigma))
    return sorted(values)
