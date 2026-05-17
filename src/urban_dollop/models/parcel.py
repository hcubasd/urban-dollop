from typing import Literal

from pydantic import BaseModel

from urban_dollop.models.carrier import Carrier
from urban_dollop.models.depot import Depot
from urban_dollop.models.zone import Zone


class Parcel(BaseModel):
    """A single parcel demand record — one row of the simulation output.

    Produced by parcel demand generation. Consumed by parcel tour
    scheduling, which bundles parcels into vehicle loads.

    ``segment``         — B2C (retailer to consumer) or C2C (consumer to consumer).
    ``fulfilment_type`` — Hubspoke (depot → door) or Hyperconnected
                          (local-to-local or crowdshipped).
    ``locker_zone``     — the zone containing the parcel locker, if redirected.
    """

    parcel_id: int
    origin_zone: Zone
    destination_zone: Zone
    depot: Depot
    carrier: Carrier
    vehicle_type: int
    locker_zone: Zone | None
    segment: Literal["B2C", "C2C"]
    local_to_local: bool
    crowdshipping_eligible: bool
    fulfilment_type: Literal["Hubspoke", "Hyperconnected"]
