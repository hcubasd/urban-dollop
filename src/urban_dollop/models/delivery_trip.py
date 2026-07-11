from pathlib import Path
from typing import Self

from pydantic import BaseModel

from urban_dollop.helpers.read_csv import read_csv


class DeliveryTrip(BaseModel):
    """A single trip leg within a delivery tour.

    One record per (origin → stop) or (stop → stop) movement. Multiple
    DeliveryTrip records share a tour_id; trip_id is the sequential
    position of this leg within that tour. The final leg returns to the
    tour origin (n_parcels == 0).

    Produced by schedule_parcel_deliveries() and consumed by the
    traffic assignment module.
    """

    tour_id: int
    trip_id: int
    carrier: str
    origin_zone_id: int
    destination_zone_id: int
    n_parcels: int
    vehicle_id: int

    @classmethod
    def from_file(cls, path: str | Path, columns: dict[str, str] = {}) -> list[Self]:
        fields = list(cls.model_fields)
        required = [n for n, fi in cls.model_fields.items() if fi.is_required()]
        records = read_csv(path, columns, fields, required)
        return [cls(**r) for r in records]

    @classmethod
    def to_file(cls, trips: list["DeliveryTrip"], path: str | Path) -> None:
        from urban_dollop.helpers.write_csv import write_csv

        write_csv([t.model_dump() for t in trips], path)
