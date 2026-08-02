from urban_dollop.helpers.random_count import random_count


def distinct_values(n, sigma):
    """n distinct positive integers, sorted, each candidate drawn the same
    way random_count draws a count (ceil(lognormal(0, sigma))). Unlike a
    terminal output value (effect, threshold), this plays stratum_value's
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
        values.add(random_count(sigma))
    return sorted(values)
