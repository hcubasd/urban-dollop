from urban_dollop.helpers.random_count import random_count


def distinct_values(n):
    """n distinct positive integers, sorted. Each candidate drawn the same
    way random_count draws a count (ceil(lognormal(0, 1))), but fixed at
    sigma=1.0 always -- this produces magnitudes (e.g. resource levels), not
    counts, so --sigma never reaches it. Duplicates are re-drawn: two
    ordinal levels sharing a value would mean two categories mapping to the
    identical real-world quantity, which has no meaningful interpretation.
    """
    values = set()
    while len(values) < n:
        values.add(random_count(1.0))
    return sorted(values)
