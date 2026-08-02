from urban_dollop.helpers.fill_thresholds import fill_thresholds
from urban_dollop.helpers.random_resources import random_resources


def capacity_thresholds(rows=None, sigma=1.0):
    """rows: existing resource/resource_level/threshold rows (threshold may
    be None throughout). None means nothing exists yet -- invent the shape
    too. Returns rows with every empty threshold filled.
    """
    if rows is None:
        rows = random_resources(sigma)
    return fill_thresholds(rows)
