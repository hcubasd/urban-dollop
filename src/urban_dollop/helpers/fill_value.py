import random


def fill_value(rows, field):
    """New list of rows with every None (or NaN) entry in `field` replaced
    by a fresh Normal(0, 1) draw -- fixed, independent of --sigma, since
    this produces the value itself, not a count of anything. Rows where
    `field` is already set are returned unchanged. Rows where `field` is
    entirely absent (as opposed to present-but-None) are also returned
    unchanged, and the key is never added -- absence means "not eligible,
    not applicable," a permanent state this function has no business
    overriding, distinct from None which means "eligible, not yet filled."
    """
    filled = []
    for row in rows:
        if field in row:
            value = row[field]
            if value is None or (isinstance(value, float) and value != value):  # NaN != NaN
                row = {**row, field: random.normalvariate(0.0, 1.0)}
        filled.append(row)
    return filled
