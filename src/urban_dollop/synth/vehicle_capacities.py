import math
import random

from urban_dollop.helpers.random_count import random_count


def vehicle_capacities(pairs=None, sigma=1.0):
    """One row per (vehicle, resource) pair: vehicle, resource, and a
    capacity. pairs=None means nothing exists yet -- invent both the
    counts (random_count(sigma) for n_vehicles and n_resources, the only
    place --sigma acts) and the full cross product of vehicle_1,
    vehicle_2, ... x resource_1, resource_2, ... . pairs given means the
    shape is already decided -- capacities get synthesized for exactly
    those pairs, in that order, ignoring sigma for the counts. Given pairs
    don't need to be a full cross product, same reasoning as
    vehicle_velocities.

    capacity is a value, not a count, despite needing the same "positive
    whole number" shape a count needs -- a vehicle can carry 12 pallets,
    not 12.7, but that's a domain constraint on this value's type, not an
    indication it should be sigma-driven (unlike resource_level in
    capacities.csv/needs.csv, which legitimately is sigma-driven because
    it plays a dual shape-defining role capacity doesn't have here). So
    it's fixed regardless of sigma, drawn with the same shape random_count
    uses (ceil(lognormvariate(0, 1))) but as a literal, not parameterized
    by --sigma.
    """
    if pairs is None:
        vehicles = [f"vehicle_{i + 1}" for i in range(random_count(sigma))]
        resources = [f"resource_{i + 1}" for i in range(random_count(sigma))]
        pairs = [{"vehicle": vehicle, "resource": resource} for vehicle in vehicles for resource in resources]
    return [
        {
            "vehicle": pair["vehicle"],
            "resource": pair["resource"],
            "capacity": math.ceil(random.lognormvariate(0.0, 1.0)),
        }
        for pair in pairs
    ]
