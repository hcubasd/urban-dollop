import random

from urban_dollop.helpers.random_count import random_count

GRADIENT_BINS = [-6, -4, -2, 0, 2, 4, 6]
PAYLOAD_BINS = [0, 50, 100]


def copert_v_coefficients(rows=None, sigma=1.0):
    """One row per (vehicle_type, pollutant, gradient_bin, payload_bin)
    key, plus the COPERT V hot-emission-function coefficients alpha
    through eta and the reduction factor rf. rows=None means nothing
    exists yet -- invent the counts (random_count(sigma) for
    n_vehicle_types and n_pollutants, the only place --sigma acts) and
    the full cross product of vehicle_type_1, vehicle_type_2, ... x
    pollutant_1, pollutant_2, ... x the fixed COPERT gradient/payload
    bins. rows given means the shape is already decided -- coefficients
    get synthesized for exactly those rows, in that order, ignoring
    sigma. Given rows don't need to cover the full bin grid -- a caller
    who has no use for some combination can simply omit it.

    alpha through eta are fitted regression coefficients with no
    canonical value to anchor to (unlike vehicles.py's BPR alpha/beta,
    which have one universal textbook default regardless of what a road
    is called): here vehicle_type and pollutant are synthetic labels,
    not real COPERT taxonomy entries, so there's no principled real-world
    coefficient set to center on. Sign-free normal(0, 1), same reasoning
    as the alternative-specific constants. rf is a reduction factor,
    conventionally bounded to [0, 1] -- plain uniform draw.
    """
    if rows is None:
        vehicle_types = [f"vehicle_type_{i + 1}" for i in range(random_count(sigma))]
        pollutants = [f"pollutant_{i + 1}" for i in range(random_count(sigma))]
        rows = [
            {
                "vehicle_type": vehicle_type,
                "pollutant": pollutant,
                "gradient_bin": gradient_bin,
                "payload_bin": payload_bin,
            }
            for vehicle_type in vehicle_types
            for pollutant in pollutants
            for gradient_bin in GRADIENT_BINS
            for payload_bin in PAYLOAD_BINS
        ]
    return [
        {
            **row,
            "alpha": random.normalvariate(0.0, 1.0),
            "beta": random.normalvariate(0.0, 1.0),
            "gamma": random.normalvariate(0.0, 1.0),
            "delta": random.normalvariate(0.0, 1.0),
            "epsilon": random.normalvariate(0.0, 1.0),
            "zeta": random.normalvariate(0.0, 1.0),
            "eta": random.normalvariate(0.0, 1.0),
            "rf": random.random(),
        }
        for row in rows
    ]
