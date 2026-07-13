from pathlib import Path
from typing import Self

from pydantic import BaseModel

from urban_dollop.helpers.read_csv import read_csv
from urban_dollop.helpers.write_csv import write_csv


class ServiceTrip(BaseModel):
    """A single service vehicle trip from an origin zone to a destination zone.

    Produced by generate_service_trips() and consumed directly by the
    network assignment module.  Unlike parcel delivery trips, service trips
    have no tour structure — each record is a self-contained point-to-point
    movement.
    """

    trip_id: int
    origin_zone_id: int
    destination_zone_id: int
    vehicle_id: int

    @classmethod
    def from_file(cls, path: str | Path) -> list[Self]:
        fields = list(cls.model_fields)
        required = [n for n, fi in cls.model_fields.items() if fi.is_required()]
        records = read_csv(Path(path), {}, fields, required)
        return [cls(**r) for r in records]

    @classmethod
    def to_file(cls, trips: list["ServiceTrip"], path: str | Path) -> None:
        write_csv([t.model_dump() for t in trips], path)
