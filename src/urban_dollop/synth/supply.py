from urban_dollop.helpers.combine_resources import combine_resources


def supply(effects_rows, thresholds_rows):
    """One row per stratum combination, one column per resource, holding
    the rounded expected value of that resource's ordered-logit
    distribution -- resource is always counted in whole units, so a
    fractional expected value isn't a deliverable quantity. A combination
    with no computable value for a resource (see combine_resources)
    simply doesn't get that column set for that row, rather than a zero.
    """
    by_combo = {}
    for entry in combine_resources(effects_rows, thresholds_rows):
        combo = {k: v for k, v in entry.items() if k not in ("resource", "pmf")}
        row = by_combo.setdefault(tuple(sorted(combo.items())), combo)
        row[entry["resource"]] = round(sum(level * p for level, p in entry["pmf"]))
    return list(by_combo.values())
