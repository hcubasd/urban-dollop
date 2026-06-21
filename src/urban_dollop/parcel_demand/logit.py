import tomllib
from math import exp
from pathlib import Path

import numpy as np
import pandas as pd

from urban_dollop.helpers.validation import validate_depot_zones
from urban_dollop.models.carrier import Carrier
from urban_dollop.models.depot import Depot
from urban_dollop.models.parcel_demand import ParcelDemand
from urban_dollop.models.skim_matrix import SkimMatrix
from urban_dollop.models.zone import Zone
from urban_dollop.parcel_demand.linear import (
    _allocate_by_share,
    _validate_carrier_depots,
    _validate_carrier_shares,
)
from urban_dollop.parcel_demand.logit_config import LogitDemandConfig


def generate(
    zones: list[Zone],
    depots: list[Depot],
    carriers: list[Carrier],
    skim: SkimMatrix,
    config: LogitDemandConfig | None = None,
) -> list[ParcelDemand]:
    config = _resolve_config(config)
    _validate_carrier_shares(carriers)
    validate_depot_zones(depots, skim)
    _validate_zone_fields(zones)

    depots_by_carrier: dict[str, list[Depot]] = {}
    for d in depots:
        depots_by_carrier.setdefault(d.carrier, []).append(d)

    _validate_carrier_depots(carriers, depots_by_carrier)

    shares = [c.share for c in carriers]

    zone_raws = [_zone_daily_demand(z, config) for z in zones]

    if config.calibration_target is not None:
        raw_total = sum(zone_raws)
        if raw_total > 0:
            scale = config.calibration_target / raw_total
            zone_raws = [r * scale for r in zone_raws]

    rows = []
    for zone, raw in zip(zones, zone_raws):
        total = int(round(raw))
        if total == 0:
            continue

        allocations = _allocate_by_share(total, shares)

        for carrier, n in zip(carriers, allocations):
            if n == 0:
                continue

            carrier_depots = depots_by_carrier[carrier.name]
            times = [skim.get(d.zone_id, zone.zone_id) for d in carrier_depots]
            nearest_depot_id = carrier_depots[int(np.argmin(times))].depot_id

            rows.append(
                {
                    "destination_zone_id": zone.zone_id,
                    "depot_id": nearest_depot_id,
                    "n_parcels": n,
                }
            )

    if not rows:
        return []

    df = pd.DataFrame(rows)
    df = df.groupby(["destination_zone_id", "depot_id"], as_index=False)["n_parcels"].sum()
    return [ParcelDemand(**row) for row in df.to_dict("records")]


def _zone_daily_demand(zone: Zone, config: LogitDemandConfig) -> float:
    eta = config.beta_urbanization.get(zone.urbanization_level, 0.0)

    # Cumulative probabilities: P(X <= p) = sigmoid(mu_p - eta)
    cprobs = [1.0 / (1.0 + exp(eta - mu)) for mu in config.mu_thresholds]
    cprobs.append(1.0)  # P(X <= last level) = 1 by definition

    # Cell probabilities as consecutive differences
    probs = [cprobs[0]]
    for i in range(1, len(config.parcel_levels)):
        probs.append(cprobs[i] - cprobs[i - 1])

    # Expected parcels per person (monthly), then convert to daily
    expected_monthly_pp = sum(pr * lv for pr, lv in zip(probs, config.parcel_levels))
    return expected_monthly_pp / config.monthly_to_daily_divisor * zone.population


def _validate_zone_fields(zones: list[Zone]) -> None:
    for z in zones:
        if z.population is None:
            raise ValueError(
                f"Zone {z.zone_id}: population is required for logit demand generation."
            )
        if z.urbanization_level is None:
            raise ValueError(
                f"Zone {z.zone_id}: urbanization_level is required for logit demand generation."
            )


def _resolve_config(config: LogitDemandConfig | None) -> LogitDemandConfig:
    toml_data: dict = {}
    toml_path = Path("urban-dollop.toml")
    if toml_path.exists():
        with open(toml_path, "rb") as f:
            toml_data = tomllib.load(f).get("parcel_demand_logit", {})

    if config is not None:
        toml_data.update(config.model_dump(exclude_none=True))

    return LogitDemandConfig(**toml_data)
