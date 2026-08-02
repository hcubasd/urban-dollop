from urban_dollop.helpers.threshold_values import threshold_values


def fill_thresholds(rows):
    """New rows with every resource's thresholds filled in, grouped by
    resource and ordered by resource_level -- the largest level in each
    resource always ends up with threshold=None. Assumes threshold is None
    throughout, which the caller (cli/_io.py's read_thresholds) already
    guarantees before rows ever reach here.
    """
    by_resource = {}
    for row in rows:
        by_resource.setdefault(row["resource"], []).append(row)

    filled = []
    for levels in by_resource.values():
        ordered = sorted(levels, key=lambda r: r["resource_level"])
        mus = threshold_values(len(ordered))
        filled.extend({**row, "threshold": mu} for row, mu in zip(ordered, mus))
    return filled
