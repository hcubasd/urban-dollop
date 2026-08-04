import random

from urban_dollop.helpers.logistic import logistic
from urban_dollop.helpers.random_count import random_count
from urban_dollop.helpers.random_subset import random_subset


def departures(sigma=1.0):
    """One row per (resource, time_interval) a resource departs in:
    resource, time_interval, and a probability -- each resource's
    probabilities sum to 1 across the intervals it uses. Self-contained --
    invents its own resources and its own interval labels, independent of
    time_intervals.csv or anything else.

    random_count(sigma) is the only place --sigma acts, for n_resources
    and for the size of a shared time-slot menu (full_intervals) --
    the menu is a property of the simulated period itself, decided once,
    not derived from any one resource's needs. Each resource then draws a
    random_subset of that menu (bounded selection from an already-fixed
    set, not new invention, so deliberately not sigma-driven either) --
    same "doesn't necessarily participate in everything" pattern
    random_strata uses for resource/stratum participation.

    Within a resource's chosen intervals, probabilities come from a
    canonical ordered logit (McCullagh 1980): a single beta and
    len(intervals) - 1 sorted cutpoints (mus), both Normal(0, 1) and fixed
    regardless of sigma since they're values, not counts. logistic(mu -
    beta) turns the cutpoints into cumulative probabilities from 0 to 1;
    consecutive differences are the probability mass for each interval, in
    the same sorted order the intervals were drawn in.
    """
    n_resources = random_count(sigma)
    n_time_slots = random_count(sigma)
    full_intervals = [f"interval_{j + 1}" for j in range(n_time_slots)]

    rows = []
    for i in range(n_resources):
        resource = f"resource_{i + 1}"
        intervals = sorted(random_subset(full_intervals))
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
