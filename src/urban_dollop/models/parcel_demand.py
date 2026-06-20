from pathlib import Path
from typing import Self

from pydantic import BaseModel


class ParcelDemand(BaseModel):
    """An aggregated parcel demand flow — one row of the demand generator output.

    Represents the total number of parcels moving from a depot to a
    destination zone. Produced by generate_parcel_demand() and consumed
    by the parcel scheduling module, which assigns vehicle types.

    The origin zone is implicit: it is always the zone of the depot.
    """

    destination_zone_id: int
    depot_id: int
    n_parcels: int

    @classmethod
    def from_file(cls, path: str | Path) -> list[Self]:
        from urban_dollop.helpers.read_csv import read_csv

        records = read_csv(path, {}, list(cls.model_fields))
        return [cls(**r) for r in records]

    @classmethod
    def to_file(cls, demands: list["ParcelDemand"], path: str | Path) -> None:
        from urban_dollop.helpers.write_csv import write_csv

        write_csv([d.model_dump() for d in demands], path)
