import numpy as np
import pandas as pd

from urban_dollop.models.microhub import Microhub
from urban_dollop.models.parcel_demand import ParcelDemand
from urban_dollop.models.skim_distance import SkimDistance
from urban_dollop.models.zero_emission_zone import ZeroEmissionZone


def consolidate_microhubs(
    demands: list[ParcelDemand],
    microhubs: list[Microhub],
    zez_zones: list[ZeroEmissionZone],
    skim_distance: SkimDistance,
) -> list[ParcelDemand]:
    """Reroute parcels destined for zero-emission zones through microhubs.

    For each demand record whose destination is in a ZEZ, splits the flow
    into two legs:
      Leg A: original origin → nearest microhub (carrier-specific, by distance)
      Leg B: microhub → original destination (zero-emission last mile)

    Demands not destined for a ZEZ pass through unchanged. Output records
    with identical (origin, destination, carrier) are aggregated. Carriers
    that have parcels destined for ZEZ zones must have at least one microhub.
    """
    if not demands:
        return []

    zez_ids = {z.zone_id for z in zez_zones}

    hubs_by_carrier: dict[str, list[Microhub]] = {}
    for mh in microhubs:
        hubs_by_carrier.setdefault(mh.carrier, []).append(mh)

    zez_carriers = {d.carrier for d in demands if d.destination_zone_id in zez_ids}
    missing = sorted(zez_carriers - set(hubs_by_carrier))
    if missing:
        names = ", ".join(missing)
        raise ValueError(
            f"Carrier(s) {names} have parcels destined for ZEZ zones but no microhubs. "
            "Add microhubs for these carriers or remove them from the ZEZ zone list."
        )

    direct_rows: list[dict] = []
    leg_a_rows: list[dict] = []
    leg_b_rows: list[dict] = []

    for d in demands:
        if d.destination_zone_id not in zez_ids:
            direct_rows.append(d.model_dump())
            continue

        carrier_hubs = hubs_by_carrier[d.carrier]
        distances = [
            skim_distance.get(mh.zone_id, d.destination_zone_id)
            for mh in carrier_hubs
        ]
        nearest_mh = carrier_hubs[int(np.argmin(distances))]

        leg_a_rows.append({
            "origin_zone_id": d.origin_zone_id,
            "destination_zone_id": nearest_mh.zone_id,
            "carrier": d.carrier,
            "n_parcels": d.n_parcels,
        })
        leg_b_rows.append({
            "origin_zone_id": nearest_mh.zone_id,
            "destination_zone_id": d.destination_zone_id,
            "carrier": d.carrier,
            "n_parcels": d.n_parcels,
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
