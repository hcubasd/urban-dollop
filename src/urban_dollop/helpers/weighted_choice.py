import random


def weighted_choice(items, weights):
    """One item drawn via a single uniform(0, 1), probability proportional
    to its weight. Weights don't need to be normalized -- the total is
    computed here. Callers are responsible for excluding zero-weight
    candidates from `items` up front if a zero-weight item must never be
    selectable; this function itself will still return one if every weight
    happens to be zero (falls back to the last item, matching how
    truncated_draw's cumulative-sum pattern behaves at its boundary).
    """
    total = sum(weights)
    u = random.random() * total
    cumulative = 0.0
    for item, w in zip(items, weights):
        cumulative += w
        if u <= cumulative:
            return item
    return items[-1]
