import math
from collections import defaultdict

import numpy as np

from urban_dollop.freight_demand.config import FreightDemandConfig
from urban_dollop.models.firm import Firm
from urban_dollop.models.freight_mnl_param import FreightMNLParam
from urban_dollop.models.freight_total import FreightTotal
from urban_dollop.models.freight_vehicle_params import FreightVehicleParams
from urban_dollop.models.make_use_coefficient import MakeUseCoefficient
from urban_dollop.models.shipment import Shipment
from urban_dollop.models.shipment_size_class import ShipmentSizeClass
from urban_dollop.models.skim_matrix import SkimMatrix


def generate_freight_demand(
    firms: list[Firm],
    freight_totals: list[FreightTotal],
    make_use: list[MakeUseCoefficient],
    size_classes: list[ShipmentSizeClass],
    vehicle_params: list[FreightVehicleParams],
    mnl_params: list[FreightMNLParam],
    skim_time: SkimMatrix,
    skim_distance: SkimMatrix,
    config: FreightDemandConfig,
) -> list[Shipment]:
    """Synthesise discrete freight shipments from aggregate demand totals.

    For each logistic segment, the budget in freight_totals is disaggregated
    into individual shipments by:

    1. Drawing a receiver zone weighted by employment × use_share per sector.
    2. Drawing a sender zone weighted by employment × make_share × distance
       decay from the receiver zone.
    3. Jointly drawing shipment size class and vehicle type via a multinomial
       logit model calibrated on transport and inventory costs.
    4. Repeating until the weight budget is exhausted; the final shipment is
       capped at the remaining weight.

    Distance decay uses the logistic function
    f(c) = 1 / (1 + exp(α + β·ln c)) where c is the generalised sourcing
    cost (config.sourcing_cost_per_hour × time + config.sourcing_cost_per_km
    × distance).  The MNL transport cost uses the vehicle-specific rates in
    freight_vehicle_params together with ceil(shipment_weight / capacity)
    trips to account for load consolidation.

    Parameters
    ----------
    firms:
        Firm register, typically the output of synthesize_firms().
    freight_totals:
        Total daily weight in tonnes per logistic segment to disaggregate.
    make_use:
        Production and consumption affinities per (logistic_segment, sector).
    size_classes:
        Discrete shipment weight alternatives per logistic segment.
    vehicle_params:
        Vehicle capacity and cost rates used in the MNL.
    mnl_params:
        MNL coefficients (B_TransportCosts, B_InventoryCosts, ASC_VT_*,
        ASC_SS_*).  logistic_segment == -1 acts as a global default.
    skim_time:
        Zone-to-zone travel time matrix in seconds.
    skim_distance:
        Zone-to-zone travel distance matrix in metres.
    config:
        Synthesiser settings: seed, sourcing costs, decay α/β.
    """
    _validate_inputs(freight_totals, make_use, size_classes, vehicle_params)

    rng = np.random.default_rng(config.seed)

    n_zones = skim_time.n_zones
    zone_ids = [z.zone_id for z in skim_time.zones]
    zone_pos = {zid: i for i, zid in enumerate(zone_ids)}

    time_mat = skim_time.data.reshape(n_zones, n_zones).astype(np.float64)
    dist_mat = skim_distance.data.reshape(n_zones, n_zones).astype(np.float64)

    cost_mat = (
        config.sourcing_cost_per_hour * time_mat / 3600.0
        + config.sourcing_cost_per_km * dist_mat / 1000.0
    )
    log_cost = np.log(np.maximum(cost_mat, 1e-9))
    decay_mat = 1.0 / (1.0 + np.exp(config.distance_decay_alpha + config.distance_decay_beta * log_cost))

    make_use_by_ls = _index_make_use(make_use)
    size_classes_by_ls = _index_size_classes(size_classes)

    zone_weights_by_ls = _compute_zone_weights(firms, make_use_by_ls, zone_pos, n_zones)

    shipments: list[Shipment] = []
    shipment_id = 1

    for ft in freight_totals:
        ls = ft.logistic_segment
        budget_kg = ft.tonnes_day * 1000.0

        if budget_kg <= 0:
            continue

        recv_base, send_base = zone_weights_by_ls.get(ls, (np.zeros(n_zones), np.zeros(n_zones)))
        recv_total = recv_base.sum()
        send_total = send_base.sum()

        if recv_total == 0.0 or send_total == 0.0:
            raise ValueError(
                f"Logistic segment {ls} has zero total receive or send weight. "
                "Check that make_use_coefficients.csv covers this segment and that "
                "at least one firm has a non-zero employment in a sector with "
                "non-zero make_share or use_share."
            )

        recv_cumul = np.cumsum(recv_base) / recv_total

        sizes_ls = size_classes_by_ls[ls]
        mnl_params_ls = _build_mnl_params_for_ls(mnl_params, ls)
        sender_cumul_cache: dict[int, np.ndarray] = {}

        while budget_kg > 0:
            j = _draw(recv_cumul, rng)

            if j not in sender_cumul_cache:
                sw = send_base * decay_mat[:, j]
                sw_total = sw.sum()
                if sw_total > 0:
                    sender_cumul_cache[j] = np.cumsum(sw) / sw_total
                else:
                    sender_cumul_cache[j] = np.arange(1, n_zones + 1, dtype=np.float64) / n_zones
            i = _draw(sender_cumul_cache[j], rng)

            time_ij = time_mat[i, j]
            dist_ij = dist_mat[i, j]
            ss_idx, vt_idx = _draw_mnl(sizes_ls, vehicle_params, time_ij, dist_ij, mnl_params_ls, rng)

            chosen_sc = sizes_ls[ss_idx]
            chosen_vp = vehicle_params[vt_idx]

            weight = min(chosen_sc.weight_kg, budget_kg)
            budget_kg -= weight

            shipments.append(Shipment(
                shipment_id=shipment_id,
                origin_zone_id=zone_ids[i],
                destination_zone_id=zone_ids[j],
                logistic_segment=ls,
                vehicle_id=chosen_vp.vehicle_id,
                weight_kg=weight,
                weight_class=chosen_sc.size_class,
            ))
            shipment_id += 1

    return shipments


def _draw(cumul: np.ndarray, rng: np.random.Generator) -> int:
    u = rng.uniform()
    return int(np.searchsorted(cumul, u, side="right"))


def _draw_mnl(
    sizes: list[ShipmentSizeClass],
    vehicles: list[FreightVehicleParams],
    time_sec: float,
    dist_m: float,
    params: dict[str, float],
    rng: np.random.Generator,
) -> tuple[int, int]:
    B_tc = params.get("B_TransportCosts", 0.0)
    B_ic = params.get("B_InventoryCosts", 0.0)
    time_hr = time_sec / 3600.0
    dist_km = dist_m / 1000.0

    alts: list[tuple[int, int]] = []
    utils: list[float] = []

    for s_idx, sc in enumerate(sizes):
        asc_ss = params.get(f"ASC_SS_{sc.size_class}", 0.0)
        for v_idx, vp in enumerate(vehicles):
            asc_vt = params.get(f"ASC_VT_{vp.vehicle_id}", 0.0)
            n_trips = math.ceil(sc.weight_kg / vp.capacity_kg)
            tc = n_trips * (vp.cost_per_hour * time_hr + vp.cost_per_km * dist_km)
            utils.append(B_tc * tc + B_ic * sc.weight_kg + asc_vt + asc_ss)
            alts.append((s_idx, v_idx))

    u_arr = np.array(utils, dtype=np.float64)
    u_arr -= u_arr.max()
    probs = np.exp(u_arr)
    probs /= probs.sum()

    cumul = np.cumsum(probs)
    idx = _draw(cumul, rng)
    return alts[idx]


def _index_make_use(
    make_use: list[MakeUseCoefficient],
) -> dict[int, dict[int, tuple[float, float]]]:
    result: dict[int, dict[int, tuple[float, float]]] = defaultdict(dict)
    for mu in make_use:
        result[mu.logistic_segment][mu.employment_sector] = (mu.make_share, mu.use_share)
    return result


def _index_size_classes(
    size_classes: list[ShipmentSizeClass],
) -> dict[int, list[ShipmentSizeClass]]:
    result: dict[int, list[ShipmentSizeClass]] = defaultdict(list)
    for sc in size_classes:
        result[sc.logistic_segment].append(sc)
    return result


def _compute_zone_weights(
    firms: list[Firm],
    make_use_by_ls: dict[int, dict[int, tuple[float, float]]],
    zone_pos: dict[int, int],
    n_zones: int,
) -> dict[int, tuple[np.ndarray, np.ndarray]]:
    result: dict[int, tuple[np.ndarray, np.ndarray]] = {}
    for ls, sector_weights in make_use_by_ls.items():
        recv_w = np.zeros(n_zones)
        send_w = np.zeros(n_zones)
        for f in firms:
            z_idx = zone_pos.get(f.zone_id)
            if z_idx is None:
                continue
            make_sh, use_sh = sector_weights.get(f.employment_sector, (0.0, 0.0))
            recv_w[z_idx] += f.employment * use_sh
            send_w[z_idx] += f.employment * make_sh
        result[ls] = (recv_w, send_w)
    return result


def _build_mnl_params_for_ls(params: list[FreightMNLParam], ls: int) -> dict[str, float]:
    result: dict[str, float] = {}
    for p in params:
        if p.logistic_segment == -1:
            result[p.parameter] = p.value
    for p in params:
        if p.logistic_segment == ls:
            result[p.parameter] = p.value
    return result


def _validate_inputs(
    freight_totals: list[FreightTotal],
    make_use: list[MakeUseCoefficient],
    size_classes: list[ShipmentSizeClass],
    vehicle_params: list[FreightVehicleParams],
) -> None:
    if not vehicle_params:
        raise ValueError("vehicle_params must not be empty.")

    ls_make_use = {mu.logistic_segment for mu in make_use}
    ls_sizes = {sc.logistic_segment for sc in size_classes}

    for ft in freight_totals:
        ls = ft.logistic_segment
        if ft.tonnes_day <= 0:
            continue
        if ls not in ls_make_use:
            raise ValueError(
                f"Logistic segment {ls} in freight_totals has no entries in "
                "make_use_coefficients — add rows for this segment."
            )
        if ls not in ls_sizes:
            raise ValueError(
                f"Logistic segment {ls} in freight_totals has no shipment size "
                "classes — add rows to shipment_size_classes.csv for this segment."
            )
