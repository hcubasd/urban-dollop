from urban_dollop.helpers.fill_value import fill_value
from urban_dollop.helpers.random_strata import random_strata


def capacity_effects(rows=None, sigma=1.0):
    """rows: existing stratum/stratum_value rows plus one column per
    resource (each may be None throughout). None means nothing exists yet
    -- invent the shape too. Returns rows with every empty resource column
    filled.
    """
    if rows is None:
        rows = random_strata(sigma)
    resource_cols = [c for c in rows[0] if c not in ("stratum", "stratum_value")]
    for col in resource_cols:
        rows = fill_value(rows, col)
    return rows
