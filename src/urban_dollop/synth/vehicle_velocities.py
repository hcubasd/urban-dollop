import random

from urban_dollop.helpers.random_count import random_count


def vehicle_velocities(pairs=None, sigma=1.0):
    """One row per (vehicle, road_type) pair: vehicle, road_type, and a
    velocity. pairs=None means nothing exists yet -- invent both the
    counts (random_count(sigma) for n_vehicles and n_road_types, the only
    place --sigma acts) and the full cross product of vehicle_1,
    vehicle_2, ... x road_type_1, road_type_2, ... . pairs given means the
    shape is already decided -- velocities get synthesized for exactly
    those pairs, in that order, ignoring sigma for the counts. Given pairs
    don't need to be a full cross product -- a caller who knows a vehicle
    has no meaningful velocity on some road type can simply omit that
    pair, rather than being forced to enumerate every combination.

    velocity is a value, not a count, and gets the same deliberately
    unassuming lognormvariate(0.0, 1.0) treatment as time_intervals'
    duration and dwell_times' dwell_time -- no canonical shape to
    preserve or invent around.
    """
    if pairs is None:
        vehicles = [f"vehicle_{i + 1}" for i in range(random_count(sigma))]
        road_types = [f"road_type_{i + 1}" for i in range(random_count(sigma))]
        pairs = [{"vehicle": vehicle, "road_type": road_type} for vehicle in vehicles for road_type in road_types]
    return [
        {"vehicle": pair["vehicle"], "road_type": pair["road_type"], "velocity": random.lognormvariate(0.0, 1.0)}
        for pair in pairs
    ]
