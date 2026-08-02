from urban_dollop.helpers.random_count import random_count


def random_strata(sigma):
    """Invent a full stratum/stratum_value shape from scratch -- zone_id
    plus n_dims-1 generic stratum_i dimensions -- with one column per
    independently-invented resource, since each resource is its own
    independent additive ordered-logit model (see README), not a shared
    linear predictor. Storing resources as columns rather than repeating
    every row once per resource makes the "same stratum shape underlies
    every resource" invariant structural: no (stratum, stratum_value) row
    can end up with a different resource set than any other. Every count
    here is random_count(sigma) -- the only place --sigma acts. Returns
    rows with every resource column set to None, ready to be filled.
    zone_id values are plain integers (1, 2, ...) rather than string
    labels -- real zone IDs are typically integers, and zone_id is the
    one stratum guaranteed to exist, so it's the one place that
    distinction is worth making. Every other dimension keeps string
    labels, since there's no equivalent real-world numeric identity to
    model.
    """
    n_dims = random_count(sigma)
    zone_card = random_count(sigma)
    dims = {"zone_id": [j + 1 for j in range(zone_card)]}
    for i in range(n_dims - 1):
        card = random_count(sigma)
        dims[f"stratum_{i + 1}"] = [f"value_{j + 1}" for j in range(card)]

    n_resources = random_count(sigma)
    resources = [f"resource_{i + 1}" for i in range(n_resources)]

    rows = []
    for stratum, values in dims.items():
        for value in values:
            row = {"stratum": stratum, "stratum_value": value}
            for resource in resources:
                row[resource] = None
            rows.append(row)
    return rows
