import math
import random

# Long-format dummy-coded coefficients for an additive (main-effects, no
# interactions) ordered-logit linear predictor: one row per (stratum column,
# stratum value) pair, never one row per full combination. A combination's
# linear predictor is the sum of whichever rows apply to it -- reconstructed
# downstream, not stored here.


def slopes(strata):
    """strata: {stratum_column: [stratum_value, ...]}. One row per pair.

    slope ~ Normal(0, 1), fixed regardless of --sigma: this is the value
    being synthesized, not a count of how much to synthesize. Mean zero is
    not a convenience default -- it's what makes each slope a legitimate
    random effect (see README): a nonzero mean would be an unidentifiable
    duplicate of an intercept this design doesn't have.
    """
    rows = []
    for column, values in strata.items():
        for value in values:
            rows.append({
                "stratum_column": column,
                "stratum_value": value,
                "slope": random.normalvariate(0.0, 1.0),
            })
    return rows


def random_strata(sigma=1.0, zone_id=None):
    """Build a full strata dict: zone_id plus n_dims-1 generic stratum_i
    dimensions. Dimension count and each dimension's cardinality are both
    ceil(lognormal(0, sigma)) -- the only place --sigma acts, since these
    are counts, not values.

    zone_id: pre-supplied zone list (e.g. borrowed from a sibling slopes
    file, since supply and demand share one geography). If None, randomized
    like every other dimension.
    """
    n_dims = math.ceil(math.exp(random.normalvariate(0.0, sigma)))
    if zone_id is None:
        zone_card = math.ceil(math.exp(random.normalvariate(0.0, sigma)))
        zone_id = [f"zone_{j + 1}" for j in range(zone_card)]
    strata = {"zone_id": zone_id}
    for i in range(n_dims - 1):
        card = math.ceil(math.exp(random.normalvariate(0.0, sigma)))
        strata[f"stratum_{i + 1}"] = [f"value_{j + 1}" for j in range(card)]
    return strata
