import random

from urban_dollop.helpers.random_count import random_count


def alternative_specific_constants(pairs=None, sigma=1.0):
    """One row per (vehicle, resource) pair: vehicle, resource, and an
    alternative_specific_constant. pairs=None means nothing exists yet --
    invent both the counts (random_count(sigma) for n_vehicles and
    n_resources, the only place --sigma acts) and the full cross product
    of vehicle_1, vehicle_2, ... x resource_1, resource_2, ... . pairs
    given means the shape is already decided -- constants get synthesized
    for exactly those pairs, in that order, ignoring sigma for the counts.
    Given pairs don't need to be a full cross product, same reasoning as
    vehicle_velocities/vehicle_capacities.

    alternative_specific_constant is the discrete-choice model's ASC: the
    baseline utility of choosing this vehicle for this resource before
    time/distance are factored in. Unlike vehicle_capacities' capacity,
    it's genuinely unrestricted in sign by definition -- one alternative
    is typically normalized to zero and the rest float above or below it
    -- so it gets the same Normal(0, 1) treatment as every other effect
    coefficient in this pipeline (supply_effects and friends), fixed
    regardless of sigma since it's a value, not a count.
    """
    if pairs is None:
        vehicles = [f"vehicle_{i + 1}" for i in range(random_count(sigma))]
        resources = [f"resource_{i + 1}" for i in range(random_count(sigma))]
        pairs = [{"vehicle": vehicle, "resource": resource} for vehicle in vehicles for resource in resources]
    return [
        {
            "vehicle": pair["vehicle"],
            "resource": pair["resource"],
            "alternative_specific_constant": random.normalvariate(0.0, 1.0),
        }
        for pair in pairs
    ]
