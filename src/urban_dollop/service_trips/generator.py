import numpy as np

from urban_dollop.models.service_trip import ServiceTrip
from urban_dollop.models.service_trip_rate import ServiceTripRate
from urban_dollop.models.service_vehicle_share import ServiceVehicleShare
from urban_dollop.models.skim_matrix import SkimMatrix
from urban_dollop.models.zone_employment import ZoneEmployment
from urban_dollop.service_trips.config import ServiceTripConfig


def generate_service_trips(
    zone_employment: list[ZoneEmployment],
    trip_rates: list[ServiceTripRate],
    vehicle_shares: list[ServiceVehicleShare],
    skim_time: SkimMatrix,
    config: ServiceTripConfig,
) -> list[ServiceTrip]:
    """Generate discrete service vehicle trips from zone employment data.

    Trip production for each zone is the sum over sectors of
    employment × trips_per_employee.  Fractional counts are resolved
    stochastically (floor + Bernoulli draw on the remainder).  Each trip's
    destination zone is drawn from an attraction distribution that weights
    zones by their total employment and a logistic distance-decay function
    of travel time.  Vehicle type is drawn independently from
    vehicle_shares.

    The logistic decay function is::

        f(t) = 1 / (1 + exp(α + β·ln t))

    where t is travel time in minutes from the origin to each candidate
    destination zone.  Calibrate α and β against observed service trip
    length distributions for the study area.

    Parameters
    ----------
    zone_employment:
        Employment by (zone, sector); consumed to compute both trip
        production per origin zone and attraction weights per destination.
    trip_rates:
        Daily trip production rate per employee per sector.  Sectors absent
        from this list contribute zero production.
    vehicle_shares:
        Probability of each vehicle type; must sum to 1.0.
    skim_time:
        Zone-to-zone travel time matrix in seconds.
    config:
        Seed and distance-decay parameters.
    """
    _validate_vehicle_shares(vehicle_shares)

    rng = np.random.default_rng(config.seed)

    n_zones = skim_time.n_zones
    zone_ids = [z.zone_id for z in skim_time.zones]
    zone_pos = {zid: i for i, zid in enumerate(zone_ids)}

    rate_by_sector = {r.employment_sector: r.trips_per_employee for r in trip_rates}

    total_emp = np.zeros(n_zones)
    production = np.zeros(n_zones)

    for ze in zone_employment:
        z_idx = zone_pos.get(ze.zone_id)
        if z_idx is None:
            continue
        total_emp[z_idx] += ze.employment
        rate = rate_by_sector.get(ze.employment_sector, 0.0)
        production[z_idx] += ze.employment * rate

    time_mat = skim_time.data.reshape(n_zones, n_zones).astype(np.float64)
    log_time = np.log(np.maximum(time_mat / 60.0, 1e-9))
    decay_mat = 1.0 / (1.0 + np.exp(config.distance_decay_alpha + config.distance_decay_beta * log_time))

    veh_ids = [v.vehicle_id for v in vehicle_shares]
    veh_cumul = np.cumsum([v.share for v in vehicle_shares])

    trips: list[ServiceTrip] = []
    trip_id = 1

    for i in range(n_zones):
        frac_trips = production[i]
        if frac_trips <= 0:
            continue

        n_trips = int(frac_trips)
        if rng.uniform() < (frac_trips - n_trips):
            n_trips += 1

        if n_trips == 0:
            continue

        dest_w = total_emp * decay_mat[i, :]
        dest_total = dest_w.sum()
        if dest_total > 0:
            dest_cumul = np.cumsum(dest_w) / dest_total
        else:
            dest_cumul = np.arange(1, n_zones + 1, dtype=np.float64) / n_zones

        for _ in range(n_trips):
            j = _draw(dest_cumul, rng)
            v_idx = _draw(veh_cumul, rng)
            trips.append(ServiceTrip(
                trip_id=trip_id,
                origin_zone_id=zone_ids[i],
                destination_zone_id=zone_ids[j],
                vehicle_id=veh_ids[v_idx],
            ))
            trip_id += 1

    return trips


def _draw(cumul: np.ndarray, rng: np.random.Generator) -> int:
    return int(np.searchsorted(cumul, rng.uniform(), side="right"))


def _validate_vehicle_shares(vehicle_shares: list[ServiceVehicleShare]) -> None:
    if not vehicle_shares:
        raise ValueError("vehicle_shares must not be empty.")
    total = sum(v.share for v in vehicle_shares)
    if abs(total - 1.0) > 1e-6:
        raise ValueError(
            f"service_vehicle_shares.csv shares must sum to 1.0; got {total:.6f}."
        )
