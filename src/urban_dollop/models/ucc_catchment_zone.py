from pathlib import Path
from typing import Self

from pydantic import BaseModel

from urban_dollop.helpers.read_csv import read_csv


class UCCCatchmentZone(BaseModel):
    """A zone whose parcels are eligible for UCC consolidation.

    Parcels destined for a UCC catchment zone are candidates for
    rerouting through an Urban Consolidation Centre; the fraction
    actually rerouted is controlled by the consolidation probability
    in UCCConfig. Loaded from ucc_catchment_zones.csv.
    """

    zone_id: int

    @classmethod
    def from_file(cls, path: str | Path, columns: dict[str, str] = {}) -> list[Self]:
        records = read_csv(path, columns, list(cls.model_fields))
        return [cls(**r) for r in records]
