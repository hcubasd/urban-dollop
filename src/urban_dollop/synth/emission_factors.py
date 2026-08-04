import random

from urban_dollop.helpers.random_count import random_count


def emission_factors(pairs=None, sigma=1.0):
    """One row per (vehicle_type, pollutant) pair: vehicle_type, pollutant,
    and an emission_factor. pairs=None means nothing exists yet -- invent
    both the counts (random_count(sigma) for n_vehicle_types and
    n_pollutants, the only place --sigma acts) and the full cross product
    of vehicle_type_1, vehicle_type_2, ... x pollutant_1, pollutant_2, ... .
    pairs given means the shape is already decided -- emission factors get
    synthesized for exactly those pairs, in that order, ignoring sigma for
    the counts. Given pairs don't need to be a full cross product, same
    reasoning as vehicle_velocities.

    Models COPERT V's non-exhaust emissions (brake wear, tire wear, road
    surface wear, resuspension) -- deliberately flat per (vehicle_type,
    pollutant), unlike copert_v_coefficients' gradient/payload-stratified
    hot-exhaust coefficients, because non-exhaust factors aren't
    gradient/payload dependent in COPERT V's own methodology. They scale
    with speed and vehicle weight instead, which is a network_emissions
    concern (via network_loads' velocity), not something this file's
    shape needs to carry.

    emission_factor is a value, not a count, and gets the same
    deliberately unassuming lognormvariate(0.0, 1.0) treatment as
    vehicle_velocities' velocity -- no canonical shape to preserve or
    invent around.
    """
    if pairs is None:
        vehicle_types = [f"vehicle_type_{i + 1}" for i in range(random_count(sigma))]
        pollutants = [f"pollutant_{i + 1}" for i in range(random_count(sigma))]
        pairs = [
            {"vehicle_type": vehicle_type, "pollutant": pollutant}
            for vehicle_type in vehicle_types
            for pollutant in pollutants
        ]
    return [
        {
            "vehicle_type": pair["vehicle_type"],
            "pollutant": pair["pollutant"],
            "emission_factor": random.lognormvariate(0.0, 1.0),
        }
        for pair in pairs
    ]
