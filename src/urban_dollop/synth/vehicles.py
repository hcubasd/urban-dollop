import random

from urban_dollop.helpers.random_count import random_count


def vehicles(vehicle_list=None, sigma=1.0):
    """One row per vehicle: vehicle, vehicle_type, bpr_alpha, bpr_beta,
    time_coefficient, distance_coefficient, and pcu. vehicle_list=None
    means nothing exists yet -- invent both the count (random_count(sigma),
    the only place --sigma acts for the vehicle roster itself) and the
    labels (vehicle_1, vehicle_2, ...). vehicle_list given means the shape
    is already decided -- the six value columns get synthesized for
    exactly those vehicles, in that order, ignoring sigma for that count.

    vehicle_type is drawn from its own invented vocabulary
    (vehicle_type_1, vehicle_type_2, ...), sized by random_count(sigma) --
    this stays sigma-driven even in the given-vehicle_list case, the same
    way network's road_type vocabulary stays sigma-driven even when
    geometry is given: --sigma always throws once vehicles.csv already
    exists, so a caller can never actually exercise that control either
    way, whichever branch happens to run internally.

    bpr_alpha/bpr_beta (the BPR congestion function's parameters,
    t = t0 * (1 + alpha * (v/c)^beta)) are triangular, not lognormal,
    unlike every other positive value in this pipeline -- both have a
    well-known real convention (the 1964 Bureau of Public Roads defaults,
    alpha=0.15, beta=4) and a well-known calibrated range in the
    transportation literature (roughly alpha in [0.05, 2], beta in
    [2, 10]), so triangular's hard bounds plus a mode at the standard
    value map onto that knowledge directly -- the same reasoning
    network's grade uses triangular(-6, 6, 0) instead of an unbounded
    distribution.

    time_coefficient/distance_coefficient are the discrete-choice model's
    marginal utility of route time/distance -- unlike alternative_specific_
    constant, these aren't sign-free: a longer route should never look
    more attractive, so they're forced negative (a positive draw would be
    a real modeling error, not just an unusual value). No real-world
    magnitude convention exists for them the way BPR's parameters have one,
    since route_time/route_dist are in this pipeline's own arbitrary
    units, so the magnitude stays unassuming (lognormal), only the sign is
    constrained.

    pcu (passenger-car-unit equivalent) stays a plain unassuming positive
    value -- median 1.0 already coincides with the real PCU baseline for a
    car, and there's no way to tie it more precisely to vehicle_type here
    since those labels are synthetic, not real categories with known PCU
    multipliers.
    """
    if vehicle_list is None:
        vehicle_list = [f"vehicle_{i + 1}" for i in range(random_count(sigma))]

    vehicle_types = [f"vehicle_type_{i + 1}" for i in range(random_count(sigma))]

    return [
        {
            "vehicle": vehicle,
            "vehicle_type": random.choice(vehicle_types),
            "bpr_alpha": random.triangular(0.05, 2.0, 0.15),
            "bpr_beta": random.triangular(2.0, 10.0, 4.0),
            "time_coefficient": -random.lognormvariate(0.0, 1.0),
            "distance_coefficient": -random.lognormvariate(0.0, 1.0),
            "pcu": random.lognormvariate(0.0, 1.0),
        }
        for vehicle in vehicle_list
    ]
