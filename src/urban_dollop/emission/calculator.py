from collections import defaultdict

import numpy as np

from urban_dollop.emission.config import EmissionCalculationConfig
from urban_dollop.models.emission_factor import EmissionFactor
from urban_dollop.models.link_emission import LinkEmission
from urban_dollop.models.loaded_link import LoadedLink


def calculate_emissions(
    loaded_links: list[LoadedLink],
    emission_factors: list[EmissionFactor],
    config: EmissionCalculationConfig | None = None,
) -> list[LinkEmission]:
    """Calculate pollutant emissions for each loaded network link.

    For each (link, vehicle, pollutant) combination, computes total grams
    emitted using COPERT V emission factors with bilinear interpolation over
    road gradient and vehicle load.

    COPERT V formula:
      EF [g/km] = (α·V² + β·V + γ + δ/V) / (ε·V² + ζ·V + η) · (1 − RF)

    Gradient is clamped to the range of gradient bins in emission_factors.
    Fill rate maps [0, 1] onto the load_pct axis [0, 100].

    Args:
        loaded_links: Network links with trip counts from assign-network.
        emission_factors: COPERT V factor table; one row per
            (vehicle_id, pollutant, gradient_pct, load_pct) cell.
        config: Speed by road type (km/h) and vehicle fill rate [0, 1].

    Returns:
        One LinkEmission per (link_id, vehicle_id, hour, pollutant).
    """
    if not loaded_links or not emission_factors:
        return []
    if config is None:
        raise ValueError(
            "EmissionCalculationConfig is required. "
            "Provide speed_kmh per road type and fill_rate."
        )

    grad_bins = sorted({ef.gradient_pct for ef in emission_factors})
    load_bins = sorted({ef.load_pct for ef in emission_factors})
    load_pct = config.fill_rate * 100.0

    # (vehicle_id, pollutant) -> {(gradient_pct, load_pct): EmissionFactor}
    factor_table: dict[
        tuple[int, str], dict[tuple[float, float], EmissionFactor]
    ] = defaultdict(dict)
    for ef in emission_factors:
        factor_table[(ef.vehicle_id, ef.pollutant)][(ef.gradient_pct, ef.load_pct)] = ef

    # vehicle_id -> list of pollutants available
    pollutants_by_vehicle: dict[int, list[str]] = defaultdict(list)
    for v_id, pollutant in factor_table:
        pollutants_by_vehicle[v_id].append(pollutant)

    _validate_vehicle_coverage(loaded_links, set(pollutants_by_vehicle))
    _validate_road_type_coverage(loaded_links, config.speed_kmh)
    _validate_factor_grid(factor_table, grad_bins, load_bins)

    results: list[LinkEmission] = []
    for link in loaded_links:
        speed = config.speed_kmh[link.road_type]
        for pollutant in sorted(pollutants_by_vehicle[link.vehicle_id]):
            factors = factor_table[(link.vehicle_id, pollutant)]
            ef_g_per_km = _interpolate_ef(
                factors, grad_bins, load_bins, link.grade_pct, load_pct, speed
            )
            emission_g = link.n_trips * (link.distance_m / 1000.0) * ef_g_per_km
            results.append(
                LinkEmission(
                    link_id=link.link_id,
                    vehicle_id=link.vehicle_id,
                    hour=link.hour,
                    pollutant=pollutant,
                    n_trips=link.n_trips,
                    distance_m=link.distance_m,
                    grade_pct=link.grade_pct,
                    emission_g=emission_g,
                )
            )

    return results


def _copert_v_ef(ef: EmissionFactor, speed_kmh: float) -> float:
    v = speed_kmh
    numerator = ef.alpha * v**2 + ef.beta * v + ef.gamma + ef.delta / v
    denominator = ef.epsilon * v**2 + ef.zeta * v + ef.eta
    return (numerator / denominator) * (1.0 - ef.rf)


def _interpolate_ef(
    factors: dict[tuple[float, float], EmissionFactor],
    grad_bins: list[float],
    load_bins: list[float],
    grade_pct: float,
    load_pct: float,
    speed_kmh: float,
) -> float:
    grade_clamped = float(np.clip(grade_pct, grad_bins[0], grad_bins[-1]))

    ef_at_load: list[float] = []
    for lp in load_bins:
        ef_at_grad = [_copert_v_ef(factors[(gp, lp)], speed_kmh) for gp in grad_bins]
        ef_at_load.append(float(np.interp(grade_clamped, grad_bins, ef_at_grad)))

    return float(np.interp(load_pct, load_bins, ef_at_load))


def _validate_vehicle_coverage(
    loaded_links: list[LoadedLink],
    vehicles_with_factors: set[int],
) -> None:
    missing = {l.vehicle_id for l in loaded_links} - vehicles_with_factors
    if missing:
        raise ValueError(
            f"Vehicle IDs {sorted(missing)} appear in loaded_links but have "
            "no emission factors. Add rows to emission_factors.csv for each vehicle."
        )


def _validate_road_type_coverage(
    loaded_links: list[LoadedLink],
    speed_kmh: dict[str, float],
) -> None:
    missing = {l.road_type for l in loaded_links} - set(speed_kmh)
    if missing:
        raise ValueError(
            f"Road types {sorted(missing)} appear in loaded_links but have no "
            "speed configured. Add entries to [emission_calculation.speed_kmh] "
            "in urban-dollop.toml."
        )


def _validate_factor_grid(
    factor_table: dict[tuple[int, str], dict[tuple[float, float], EmissionFactor]],
    grad_bins: list[float],
    load_bins: list[float],
) -> None:
    expected = {(g, l) for g in grad_bins for l in load_bins}
    for (v_id, pollutant), factors in factor_table.items():
        missing = expected - set(factors)
        if missing:
            missing_str = sorted(missing)
            raise ValueError(
                f"Incomplete emission factor grid for vehicle {v_id}, "
                f"pollutant '{pollutant}': missing (gradient_pct, load_pct) "
                f"cells {missing_str}. Each vehicle/pollutant must cover all "
                "gradient × load combinations."
            )
