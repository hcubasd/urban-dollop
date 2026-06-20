from pathlib import Path
from typing import Self

from pydantic import BaseModel

from urban_dollop.helpers.read_gpkg import read_gpkg


class Depot(BaseModel):
    """A parcel distribution depot — the physical origin of deliveries."""

    depot_id: int
    zone_id: int
    carrier: str

    @classmethod
    def from_file(cls, path: str | Path, columns: dict[str, str] = {}) -> list[Self]:
        records = read_gpkg(path, columns, list(cls.model_fields))
        return [cls(**r) for r in records]
