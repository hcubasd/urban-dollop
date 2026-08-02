from urban_dollop.helpers.fill_value import fill_value
from urban_dollop.helpers.random_strata import random_strata


def supply_effects(rows=None, sigma=1.0):
    """rows: existing stratum_column/stratum_value/effect rows (effect may
    be None throughout). None means nothing exists yet -- invent the shape
    too. Returns rows with every empty effect filled.
    """
    if rows is None:
        rows = random_strata(sigma)
    return fill_value(rows, "effect")
