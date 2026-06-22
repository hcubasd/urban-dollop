import numpy as np
import pandas as pd

from urban_dollop.consolidation.ucc_config import UCCConfig
from urban_dollop.models.parcel_demand import ParcelDemand
from urban_dollop.models.skim_distance import SkimDistance
from urban_dollop.models.ucc import UCC
from urban_dollop.models.ucc_catchment_zone import UCCCatchmentZone


def consolidate_uccs(
    demands: list[ParcelDemand],
    uccs: list[UCC],
    catchment_zones: list[UCCCatchmentZone],
    skim_distance: SkimDistance,
    config: UCCConfig,
) -> list[ParcelDemand]:
    """Reroute a fraction of catchment-zone parcels through Urban Consolidation Centres.

    For each demand record whose destination is in a UCC catchment zone,
    a fraction (config.probability) of parcels are rerouted through the
    nearest UCC — nearest defined as the UCC minimising total two-leg
    distance (origin → UCC + UCC → destination). The rerouted flow is
    split into:
      Leg A: original origin → UCC
      Leg B: UCC → original destination

    Unrerouted parcels remain as a direct flow. Demands not destined for
    a catchment zone pass through unchanged. Output records with identical
    (origin, destination, carrier) are aggregated.
    """
    if not demands:
        return []

    catchment_ids = {z.zone_id for z in catchment_zones}

    if any(d.destination_zone_id in catchment_ids for d in demands) and not uccs:
        raise ValueError(
            "Demands are destined for UCC catchment zones but no UCCs are configured. "
            "Add UCCs or remove catchment zone designations."
        )

    direct_rows: list[dict] = []
    leg_a_rows: list[dict] = []
    leg_b_rows: list[dict] = []

    for d in demands:
        if d.destination_zone_id not in catchment_ids:
            direct_rows.append(d.model_dump())
            continue

        rerouted = round(d.n_parcels * config.probability)
        remaining = d.n_parcels - rerouted

        if rerouted == 0:
            direct_rows.append(d.model_dump())
            continue

        # Nearest UCC minimises total two-leg distance
        scores = [
            skim_distance.get(d.origin_zone_id, ucc.zone_id)
            + skim_distance.get(ucc.zone_id, d.destination_zone_id)
            for ucc in uccs
        ]
        nearest_ucc = uccs[int(np.argmin(scores))]

        if remaining > 0:
            direct_rows.append({
                "origin_zone_id": d.origin_zone_id,
                "destination_zone_id": d.destination_zone_id,
                "carrier": d.carrier,
                "n_parcels": remaining,
            })

        leg_a_rows.append({
            "origin_zone_id": d.origin_zone_id,
            "destination_zone_id": nearest_ucc.zone_id,
            "carrier": d.carrier,
            "n_parcels": rerouted,
        })
        leg_b_rows.append({
            "origin_zone_id": nearest_ucc.zone_id,
            "destination_zone_id": d.destination_zone_id,
            "carrier": d.carrier,
            "n_parcels": rerouted,
        })

    return _aggregate(direct_rows) + _aggregate(leg_a_rows) + _aggregate(leg_b_rows)


def _aggregate(rows: list[dict]) -> list[ParcelDemand]:
    if not rows:
        return []
    df = pd.DataFrame(rows)
    df = df.groupby(
        ["origin_zone_id", "destination_zone_id", "carrier"], as_index=False
    )["n_parcels"].sum()
    return [ParcelDemand(**row) for row in df.to_dict("records")]
