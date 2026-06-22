from pathlib import Path
from typing import Self

from pydantic import BaseModel


class ParcelDemand(BaseModel):
    """An aggregated parcel demand flow — one row of the demand generator output.

    Represents the total number of parcels moving from an origin zone to a
    destination zone, operated by a given carrier. Produced by
    generate_parcel_demand() and generate_logit_demand(), consumed by the
    consolidation and scheduling modules.

    For direct flows (no consolidation) the origin zone is always the zone
    of the nearest depot. Consolidation modules may produce records where
    the origin is a microhub or UCC zone.
    """

    origin_zone_id: int
    destination_zone_id: int
    carrier: str
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
