import random


def truncated_draw(pmf, budget):
    """Draw a level from `pmf` (a list of (resource_level, probability)
    pairs) restricted to levels <= `budget` and renormalized, via a
    single uniform(0, 1) draw. Returns None if no level in `pmf` is <=
    budget -- infeasible, nothing to draw. The caller's job to treat that
    as a halt signal, never to invent a value the distribution doesn't
    actually support.

    Idempotent at the top end: once `budget` is at least the largest
    level in `pmf`, the truncated distribution *is* the original
    distribution, so nothing special needs to happen there -- the
    truncation only ever does real work near the bottom of the range.
    """
    feasible = [(level, p) for level, p in pmf if level <= budget]
    if not feasible:
        return None
    total = sum(p for _, p in feasible)
    u = random.random()
    cumulative = 0.0
    for level, p in feasible:
        cumulative += p / total
        if u <= cumulative:
            return level
    return feasible[-1][0]
