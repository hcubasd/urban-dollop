import random

from urban_dollop.helpers.random_count import random_count


def road_capacities(road_types=None, sigma=1.0):
    """One row per road type: road_type and a capacity. road_types=None
    means nothing exists yet -- invent both the count (random_count(sigma),
    the only place --sigma acts) and the labels (road_type_1, road_type_2,
    ...). road_types given means the shape is already decided -- capacities
    get synthesized for exactly those road types, in that order, ignoring
    sigma for the count.

    capacity is a value, not a count, and its distribution is deliberately
    unassuming (lognormvariate(0.0, 1.0), fixed regardless of sigma), same
    treatment as vehicle_velocities' velocity -- a plain continuous PCU
    figure, no whole-number constraint the way vehicle_capacities' capacity
    had.
    """
    if road_types is None:
        road_types = [f"road_type_{i + 1}" for i in range(random_count(sigma))]
    return [{"road_type": road_type, "capacity": random.lognormvariate(0.0, 1.0)} for road_type in road_types]
