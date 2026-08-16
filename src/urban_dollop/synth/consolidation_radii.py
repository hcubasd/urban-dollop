import random

from urban_dollop.helpers.random_count import random_count


def consolidation_radii(pairs=None, sigma=1.0):
    """One positive consolidation radius per (vehicle, resource) pair.

    With no supplied shape, vehicle and resource counts are synthesized
    independently and their full cross product receives a radius. Supplied
    pairs define the shape exactly. Radius is an unbounded positive value,
    so it follows the project's standard lognormal value synthesis and is
    independent of --sigma.
    """
    if pairs is None:
        vehicles = [f"vehicle_{i + 1}" for i in range(random_count(sigma))]
        resources = [f"resource_{i + 1}" for i in range(random_count(sigma))]
        pairs = [{"vehicle": vehicle, "resource": resource} for vehicle in vehicles for resource in resources]
    return [
        {
            "vehicle": pair["vehicle"],
            "resource": pair["resource"],
            "radius": random.lognormvariate(0.0, 1.0),
        }
        for pair in pairs
    ]
