from urban_dollop.helpers.combine_resources import combine_resources


def needs(effects_rows, thresholds_rows):
    """One row per (stratum combination, resource, resource_level) --
    long on the resource/level axis, since a full PMF needs multiple rows
    per stratum combination. Unlike supply/demand, nothing gets rounded
    or collapsed: this is the distribution individual agents get sampled
    from later, so it has to stay a distribution. A (combination,
    resource) pair with no computable PMF (see combine_resources) simply
    has no rows here at all.
    """
    rows = []
    for entry in combine_resources(effects_rows, thresholds_rows):
        combo = {k: v for k, v in entry.items() if k not in ("resource", "pmf")}
        for level, probability in entry["pmf"]:
            rows.append({**combo, "resource": entry["resource"], "resource_level": level, "probability": probability})
    return rows
