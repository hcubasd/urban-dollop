from urban_dollop.helpers.random_count import random_count


def random_strata(sigma):
    """Invent a full stratum/stratum_value/resource shape from scratch:
    zone_id plus n_dims-1 generic stratum_i dimensions, crossed with
    n_resources independently-invented resources -- every (stratum,
    stratum_value) pair gets its own row per resource, since each resource
    is its own independent additive ordered-logit model (see README), not
    a shared linear predictor. The stratum shape itself (which dimensions
    exist, how many values each has) is invented once and reused across
    every resource; only the resulting effect values differ per resource,
    once filled. Every count here is random_count(sigma) -- the only place
    --sigma acts. Returns rows with effect=None, ready to be filled.
    """
    n_dims = random_count(sigma)
    zone_card = random_count(sigma)
    dims = {"zone_id": [f"zone_{j + 1}" for j in range(zone_card)]}
    for i in range(n_dims - 1):
        card = random_count(sigma)
        dims[f"stratum_{i + 1}"] = [f"value_{j + 1}" for j in range(card)]

    n_resources = random_count(sigma)
    resources = [f"resource_{i + 1}" for i in range(n_resources)]

    rows = []
    for resource in resources:
        for stratum, values in dims.items():
            for value in values:
                rows.append({
                    "stratum": stratum,
                    "stratum_value": value,
                    "resource": resource,
                    "effect": None,
                })
    return rows
