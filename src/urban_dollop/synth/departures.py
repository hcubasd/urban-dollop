import random

from urban_dollop.helpers.logistic import logistic
from urban_dollop.helpers.random_count import random_count
from urban_dollop.helpers.random_subset import random_subset


def departures(pairs=None, sigma=1.0):
    """One row per (resource, time_interval) a resource departs in:
    resource, time_interval, and a probability -- each resource's
    probabilities sum to 1 across the intervals it uses.

    pairs=None means nothing exists yet -- invent both the shape (which
    resources, which intervals each one uses) and the probabilities.
    random_count(sigma) is the only place --sigma acts, twice: once for
    n_resources, and once for the size of a shared time-slot menu
    (interval_1, interval_2, ...) that's a property of the simulated
    period itself, decided once, not derived from any one resource's
    needs. Each resource then draws a random_subset of that menu --
    bounded selection from an already-fixed set, not new invention, so
    deliberately not sigma-driven either -- same "doesn't necessarily
    participate in everything" pattern random_strata uses for
    resource/stratum participation.

    pairs given (a list of {resource, time_interval} dicts, no
    probability) means the shape is already decided -- probabilities get
    synthesized for exactly those pairs, grouped by resource in whatever
    order they're given (that order carries no meaning here -- unlike
    time_intervals.csv, this file makes no chronological claim, so
    there's nothing to preserve by sorting).

    Within a resource's pairs, probabilities come from a canonical
    ordered logit (McCullagh 1980): a single beta and n - 1 sorted
    cutpoints (mus), both Normal(0, 1) and fixed regardless of sigma
    since they're values, not counts. logistic(mu - beta) turns the
    cutpoints into cumulative probabilities from 0 to 1; consecutive
    differences are the probability mass for each interval.
    """
    if pairs is None:
        n_resources = random_count(sigma)
        n_time_slots = random_count(sigma)
        full_intervals = [f"interval_{j + 1}" for j in range(n_time_slots)]
        pairs = [
            {"resource": f"resource_{i + 1}", "time_interval": interval}
            for i in range(n_resources)
            for interval in sorted(random_subset(full_intervals))
        ]

    by_resource = {}
    for pair in pairs:
        by_resource.setdefault(pair["resource"], []).append(pair["time_interval"])

    rows = []
    for resource, intervals in by_resource.items():
        beta = random.normalvariate(0.0, 1.0)
        mus = sorted(random.normalvariate(0.0, 1.0) for _ in range(len(intervals) - 1))
        cum_probs = [0.0] + [logistic(mu - beta) for mu in mus] + [1.0]
        for k, interval in enumerate(intervals):
            rows.append({
                "resource": resource,
                "time_interval": interval,
                "probability": cum_probs[k + 1] - cum_probs[k],
            })

    return rows
