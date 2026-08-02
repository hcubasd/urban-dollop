from urban_dollop.helpers.random_count import random_count


def random_strata(sigma):
    """Invent a full stratum_column/stratum_value shape from scratch:
    zone_id plus n_dims-1 generic stratum_i dimensions. Dimension count and
    each dimension's cardinality are both random_count(sigma) -- the only
    place --sigma acts, since these are counts, not values. Returns rows
    with effect=None, ready to be filled.
    """
    n_dims = random_count(sigma)
    zone_card = random_count(sigma)
    rows = [
        {"stratum_column": "zone_id", "stratum_value": f"zone_{j + 1}", "effect": None}
        for j in range(zone_card)
    ]
    for i in range(n_dims - 1):
        card = random_count(sigma)
        rows += [
            {"stratum_column": f"stratum_{i + 1}", "stratum_value": f"value_{j + 1}", "effect": None}
            for j in range(card)
        ]
    return rows
