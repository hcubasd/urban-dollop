from pathlib import Path
from typing import Self

from pydantic import BaseModel

from urban_dollop.helpers.read_csv import read_csv


class UCC(BaseModel):
    """An Urban Consolidation Centre.

    Carrier-agnostic facility where parcels from multiple carriers are
    consolidated before delivery into the catchment area. The nearest
    UCC is selected per flow by minimising total two-leg distance
    (origin → UCC + UCC → destination). Loaded from uccs.csv.
    """

    ucc_id: int
    zone_id: int

    @classmethod
    def from_file(cls, path: str | Path, columns: dict[str, str] = {}) -> list[Self]:
        records = read_csv(path, columns, list(cls.model_fields))
        return [cls(**r) for r in records]
