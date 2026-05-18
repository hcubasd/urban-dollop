import tomllib
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

    depots_by_carrier: dict[str, list[Depot]] = {}
    for d in depots:
        depots_by_carrier.setdefault(d.carrier, []).append(d)

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

        for carrier in carriers:
            carrier_depots = depots_by_carrier.get(carrier.name, [])
            if not carrier_depots:
                continue

            n = int(round(total * carrier.share))
            if n == 0:
                continue

            times = [skim.get(d.zone_id, zone.zone_id) for d in carrier_depots]
            nearest_depot_id = carrier_depots[int(np.argmin(times))].depot_id

            rows.append(
                {
                    "destination_zone_id": zone.zone_id,
                    "depot_id": nearest_depot_id,
                    "vehicle_type": config.default_vehicle_type,
                    "n_parcels": n,
                }
            )

    if not rows:
        return []

    df = pd.DataFrame(rows)
    df = df.groupby(
        ["destination_zone_id", "depot_id", "vehicle_type"], as_index=False
    )["n_parcels"].sum()

    return [ParcelDemand(**row) for row in df.to_dict("records")]


def _resolve_config(config: ParcelDemandConfig | None) -> ParcelDemandConfig:
    toml_data: dict = {}
    toml_path = Path("urban-dollop.toml")
    if toml_path.exists():
        with open(toml_path, "rb") as f:
            toml_data = tomllib.load(f).get("parcel_demand", {})

    if config is not None:
        toml_data.update(config.model_dump())

    return ParcelDemandConfig(**toml_data)
