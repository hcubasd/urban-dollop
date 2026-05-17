from typing import Literal

from urban_dollop.models.base import FileModel


class Parcel(FileModel):
    """A single parcel demand record — one row of the simulation output.

    Produced by parcel demand generation. Consumed by parcel tour
    scheduling, which bundles parcels into vehicle loads.

    ``segment``         — B2C (retailer to consumer) or C2C (consumer to consumer).
    ``fulfilment_type`` — Hubspoke (depot → door) or Hyperconnected
                          (local-to-local or crowdshipped).
    ``locker_zone``     — zone_id of the parcel locker zone, if redirected.
    """

    parcel_id: int
    origin_zone: int
    destination_zone: int
    depot_id: int
    carrier: str
    vehicle_type: int
    locker_zone: int | None
    segment: Literal["B2C", "C2C"]
    local_to_local: bool
    crowdshipping_eligible: bool
    fulfilment_type: Literal["Hubspoke", "Hyperconnected"]
