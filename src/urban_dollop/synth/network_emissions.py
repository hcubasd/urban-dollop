import bisect

from urban_dollop.synth.copert_v_coefficients import GRADIENT_BINS, PAYLOAD_BINS

_EXHAUST = "exhaust"
_NON_EXHAUST = "non-exhaust"


def _snap(value, bins):
    """The bin nearest `value`, clamped to the ends. COPERT publishes its
    coefficients on a discrete gradient/payload grid, so a link's actual
    grade and a vehicle's actual load have to land on one of them.
    """
    index = bisect.bisect_left(bins, value)
    if index == 0:
        return bins[0]
    if index == len(bins):
        return bins[-1]
    before, after = bins[index - 1], bins[index]
    return before if abs(value - before) <= abs(value - after) else after


def _hot_emission_factor(coefficients, velocity):
    """COPERT V's speed-dependent hot-exhaust emission factor in g/km:

        (a*V^2 + b*V + c + d/V) / (e*V^2 + f*V + g) * (1 - RF)

    Returns None where the function has nothing meaningful to say -- at or
    below zero speed (the d/V term is undefined, and a stationary vehicle
    isn't accruing distance-based emissions anyway) and where the
    denominator vanishes. None means "no row", deliberately distinct from
    a real computed 0.0.
    """
    if velocity <= 0:
        return None
    denominator = (
        coefficients["epsilon"] * velocity ** 2
        + coefficients["zeta"] * velocity
        + coefficients["eta"]
    )
    if denominator == 0:
        return None
    numerator = (
        coefficients["alpha"] * velocity ** 2
        + coefficients["beta"] * velocity
        + coefficients["gamma"]
        + coefficients["delta"] / velocity
    )
    return max(0.0, numerator / denominator * (1.0 - coefficients["rf"]))


def network_emissions(network_load_rows, network_rows, vehicle_rows,
                      copert_rows, emission_factor_rows):
    """One row per (link, time interval, resource, vehicle, direction, pollutant,
    source) the simulation actually emitted on: link_id, time_interval,
    vehicle, forward, pollutant, source, grams.

    Exhaust and non-exhaust are reported as separate rows sharing every
    other key, never summed into one number, because they're different
    physical mechanisms that happen to produce the same pollutant -- the
    same way the source methodology plots them side by side. A consumer
    wanting the total for a pollutant sums its two rows; one wanting to
    know how much of a PM figure is tailpipe versus brake and tire wear
    can still tell, which a pre-summed column would make impossible.

    Exhaust follows COPERT V: each load row's velocity, its link's grade,
    and its vehicles' mean load are snapped onto COPERT's published
    gradient/payload grid, the speed-dependent function gives a factor in
    g/km, and that scales by distance travelled (link length times vehicle
    count). Grade is signed relative to the link's own start-to-end order,
    so a backward traversal negates it before snapping -- which is the
    whole reason network_loads.csv carries a direction per row.

    Non-exhaust (brake wear, tire wear, road surface wear, resuspension)
    uses emission_factors.csv's flat factor, scaled by the same distance.
    It is deliberately not gradient/payload stratified and deliberately
    does not vary with velocity: COPERT V's non-exhaust factors aren't
    published against that grid, and while the source methodology notes
    non-exhaust emissions vary with speed, it gives no functional form for
    it -- inventing one here would be fabricating a relationship the
    reference doesn't specify. If a velocity dependence is wanted later,
    emission_factors.csv gaining velocity bins is the place for it.
    """
    links = {}
    for row in network_rows:
        links[row["link_id"]] = {"grade": row["grade"], "length": row["geometry"].length}

    vehicle_types = {row["vehicle"]: row["vehicle_type"] for row in vehicle_rows}

    copert = {}
    for row in copert_rows:
        key = (row["vehicle_type"], row["pollutant"], row["gradient_bin"], row["payload_bin"])
        copert[key] = row

    pollutants_by_type = {}
    for row in copert_rows:
        pollutants_by_type.setdefault(row["vehicle_type"], set()).add(row["pollutant"])

    non_exhaust = {
        (row["vehicle_type"], row["pollutant"]): row["emission_factor"]
        for row in emission_factor_rows
    }

    gradient_bins = sorted(GRADIENT_BINS)
    payload_bins = sorted(PAYLOAD_BINS)

    output = []
    for load in network_load_rows:
        link = links.get(load["link_id"])
        if link is None:
            continue
        vehicle_type = vehicle_types.get(load["vehicle"])
        if vehicle_type is None:
            continue

        distance = link["length"] * load["vehicle_count"]
        if distance <= 0:
            continue

        signed_grade = link["grade"] if load["forward"] else -link["grade"]
        gradient_bin = _snap(signed_grade, gradient_bins)
        payload_bin = _snap(load["load_pct"] * 100.0, payload_bins)

        def emit(pollutant, source, grams):
            output.append({
                "link_id": load["link_id"],
                "time_interval": load["time_interval"],
                "resource": load["resource"],
                "vehicle": load["vehicle"],
                "forward": load["forward"],
                "pollutant": pollutant,
                "source": source,
                "grams": grams,
            })

        for pollutant in sorted(pollutants_by_type.get(vehicle_type, ())):
            coefficients = copert.get((vehicle_type, pollutant, gradient_bin, payload_bin))
            if coefficients is None:
                continue
            factor = _hot_emission_factor(coefficients, load["velocity"])
            if factor is None:
                continue
            emit(pollutant, _EXHAUST, factor * distance)

        for (candidate_type, pollutant), factor in sorted(non_exhaust.items()):
            if candidate_type != vehicle_type:
                continue
            emit(pollutant, _NON_EXHAUST, factor * distance)

    return output
