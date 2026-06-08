from pathlib import Path

from pydantic import BaseModel


class DeliveryTrip(BaseModel):
    """A single trip leg within a delivery tour.

    One record per (depot → stop) or (stop → stop) movement. Multiple
    DeliveryTrip records share a tour_id; trip_id is the sequential
    position of this leg within that tour.

    Produced by schedule_parcel_deliveries() and consumed by the
    traffic assignment module.
    """

    tour_id: int
    trip_id: int
    depot_id: int
    carrier: str
    origin_zone_id: int
    destination_zone_id: int
    n_parcels: int
    vehicle_id: int

    @classmethod
    def to_file(cls, trips: list["DeliveryTrip"], path: str | Path) -> None:
        from urban_dollop.models.helpers.write_csv import write_csv

        write_csv([t.model_dump() for t in trips], path)
