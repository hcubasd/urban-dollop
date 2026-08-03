import itertools

from urban_dollop.helpers.logistic import logistic


def _is_empty(value):
    return value is None or (isinstance(value, float) and value != value)  # NaN != NaN


def _dim_values(effects_rows):
    dims = {}
    for row in effects_rows:
        dims.setdefault(row["stratum"], set()).add(row["stratum_value"])
    return {stratum: sorted(values, key=str) for stratum, values in dims.items()}


def _effect_lookup(effects_rows):
    resource_cols = {c for row in effects_rows for c in row if c not in ("stratum", "stratum_value")}
    lookup = {}
    for row in effects_rows:
        for resource in resource_cols:
            if resource in row and not _is_empty(row[resource]):
                lookup[(row["stratum"], row["stratum_value"], resource)] = row[resource]
    return lookup, resource_cols


def _thresholds_by_resource(thresholds_rows):
    by_resource = {}
    for row in thresholds_rows:
        by_resource.setdefault(row["resource"], []).append(row)
    for levels in by_resource.values():
        levels.sort(key=lambda r: r["resource_level"])
    return by_resource


def combine_resources(effects_rows, thresholds_rows):
    """For each resource in the intersection of effects_rows' resource
    columns and thresholds_rows' resource values, and for each full
    cartesian combination of effects_rows' stratum dimensions, compute
    that resource's discrete PMF via the ordered-logit model (McCullagh
    1980): beta is the sum of each dimension's effect for its value in
    this combination, cum_probs = [0, logistic(t0-beta), ...,
    logistic(t_{k-2}-beta), 1], and the PMF is the consecutive
    differences, one per resource_level.

    A (combination, resource) pair is omitted entirely -- never given a
    zero-contribution stand-in -- if *any* constituent dimension-value
    lacks an effect for that resource. The additive model's beta is
    undefined if any term is undefined, not zero; a resource missing from
    the intersection is the same kind of absence at the whole-file level.
    Both are "no answer available," not "the answer is zero" -- zero is
    itself a real, reachable resource_level, so it can never double as an
    undefined-data marker.

    Returns a list of dicts, one per computable (combination, resource)
    pair: every stratum dimension's value for that combination, plus
    "resource" and "pmf" (a list of (resource_level, probability) tuples,
    ascending by level).
    """
    dims = _dim_values(effects_rows)
    effect_lookup, resource_cols = _effect_lookup(effects_rows)
    thresholds_by_resource = _thresholds_by_resource(thresholds_rows)
    resources = resource_cols & set(thresholds_by_resource)

    dim_names = list(dims)
    entries = []
    for resource in resources:
        levels = thresholds_by_resource[resource]
        level_values = [r["resource_level"] for r in levels]
        thresholds = [r["threshold"] for r in levels if not _is_empty(r["threshold"])]

        for combo_values in itertools.product(*(dims[name] for name in dim_names)):
            combo = dict(zip(dim_names, combo_values))
            beta = 0.0
            for dim_name, value in combo.items():
                key = (dim_name, value, resource)
                if key not in effect_lookup:
                    beta = None
                    break
                beta += effect_lookup[key]
            if beta is None:
                continue

            cum_probs = [0.0] + [logistic(mu - beta) for mu in thresholds] + [1.0]
            pmf = [(level_values[k], cum_probs[k + 1] - cum_probs[k]) for k in range(len(level_values))]
            entries.append({**combo, "resource": resource, "pmf": pmf})
    return entries
