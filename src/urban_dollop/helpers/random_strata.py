from urban_dollop.helpers.random_count import random_count
from urban_dollop.helpers.random_subset import random_subset


def random_strata(sigma):
    """Invent a full stratum/stratum_value shape from scratch -- zone_id
    plus n_dims-1 generic stratum_i dimensions -- with one column per
    independently-invented resource, since each resource is its own
    independent additive ordered-logit model (see README), not a shared
    linear predictor. Every count here is random_count(sigma) -- the only
    place --sigma acts. zone_id values are plain integers (1, 2, ...)
    rather than string labels -- real zone IDs are typically integers, and
    zone_id is the one stratum guaranteed to exist, so it's the one place
    that distinction is worth making. Every other dimension keeps string
    labels, since there's no equivalent real-world numeric identity to
    model.

    Each resource independently gets a random_subset of rows to apply to
    (never all of them by construction, never none) -- a stratum
    genuinely may not participate in every resource's market, so not
    every row gets every resource column. A row not chosen for a given
    resource simply doesn't get that key at all, rather than an explicit
    None: that key-presence distinction is what lets fill_value tell
    "eligible, not yet filled" apart from "not applicable, leave alone."
    Rows chosen for a resource get that key set to None, ready to be
    filled.
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
            rows.append({"stratum": stratum, "stratum_value": value})

    for resource in resources:
        for row in random_subset(rows):
            row[resource] = None

    return rows
