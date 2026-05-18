from pydantic import BaseModel


class ParcelDemand(BaseModel):
    """An aggregated parcel demand flow — one row of the demand generator output.

    Represents the total number of parcels moving from a depot to a
    destination zone, for a given carrier and vehicle type. Produced by
    generate_parcel_demand() and consumed by the parcel scheduling module.

    The origin zone is implicit: it is always the zone of the depot.
    """

    destination_zone_id: int
    depot_id: int
    vehicle_type: int
    n_parcels: int
