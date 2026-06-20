import tomllib
from math import floor, isclose
from pathlib import Path

import numpy as np
import pandas as pd

from urban_dollop.models.carrier import Carrier
from urban_dollop.models.depot import Depot
from urban_dollop.models.parcel_demand import ParcelDemand
from urban_dollop.models.skim_matrix import SkimMatrix
from urban_dollop.models.zone import Zone
from urban_dollop.parcel_demand.config import ParcelDemandConfig


def generate_parcel_demand(
    zones: list[Zone],
    depots: list[Depot],
    carriers: list[Carrier],
    skim: SkimMatrix,
    config: ParcelDemandConfig | None = None,
) -> list[ParcelDemand]:
    config = _resolve_config(config)
    _validate_carrier_shares(carriers)
    _validate_depot_zones(depots, skim)

    depots_by_carrier: dict[str, list[Depot]] = {}
    for d in depots:
        depots_by_carrier.setdefault(d.carrier, []).append(d)

    _validate_carrier_depots(carriers, depots_by_carrier)

    shares = [c.share for c in carriers]

    rows = []
    for zone in zones:
        total = int(
            round(
                zone.households
                * config.parcels_per_household
                / config.delivery_success_b2c
                + zone.employment
                * config.parcels_per_employee
                / config.delivery_success_b2b
            )
        )
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
    df = df.groupby(["destination_zone_id", "depot_id"], as_index=False)[
        "n_parcels"
    ].sum()

    return [ParcelDemand(**row) for row in df.to_dict("records")]


def _allocate_by_share(total: int, shares: list[float]) -> list[int]:
    """Distribute total across shares as integers using the largest-remainder method.

    Guarantees sum(result) == total, avoiding the silent parcel loss that
    occurs when independently rounding each carrier's fractional allocation.
    """
    quotas = [total * s for s in shares]
    floors = [floor(q) for q in quotas]
    remaining = total - sum(floors)
    if remaining > 0:
        remainders = [q - f for q, f in zip(quotas, floors)]
        for i in sorted(range(len(remainders)), key=lambda i: -remainders[i])[:remaining]:
            floors[i] += 1
    return floors


def _resolve_config(config: ParcelDemandConfig | None) -> ParcelDemandConfig:
    toml_data: dict = {}
    toml_path = Path("urban-dollop.toml")
    if toml_path.exists():
        with open(toml_path, "rb") as f:
            toml_data = tomllib.load(f).get("parcel_demand", {})

    if config is not None:
        toml_data.update(config.model_dump())

    return ParcelDemandConfig(**toml_data)


def _validate_depot_zones(depots: list[Depot], skim: SkimMatrix) -> None:
    missing = [d for d in depots if d.zone_id not in skim._pos]
    if missing:
        ids = ", ".join(str(d.depot_id) for d in missing)
        zones = ", ".join(str(d.zone_id) for d in missing)
        raise ValueError(
            f"Depot(s) {ids} have zone_id(s) {zones} not present in the skim matrix. "
            "Add these zones to your zones file or remove the depots."
        )


def _validate_carrier_depots(
    carriers: list[Carrier],
    depots_by_carrier: dict[str, list[Depot]],
) -> None:
    missing = [c for c in carriers if c.share > 0 and not depots_by_carrier.get(c.name)]
    if missing:
        names = ", ".join(c.name for c in missing)
        raise ValueError(
            f"Carrier(s) {names} have non-zero market share but no depots. "
            "Add depots for these carriers or set their share to 0."
        )


def _validate_carrier_shares(carriers: list[Carrier]) -> None:
    total_share = sum(carrier.share for carrier in carriers)
    if not isclose(total_share, 1.0, rel_tol=0.0, abs_tol=1e-3):
        raise ValueError(f"Carrier shares must sum to 1.0, got {total_share:.12g}.")
    if not isclose(total_share, 1.0, rel_tol=0.0, abs_tol=1e-9):
        for carrier in carriers:
            carrier.share /= total_share
