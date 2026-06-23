from pathlib import Path
from typing import Self

from pydantic import BaseModel

from urban_dollop.helpers.read_csv import read_csv
from urban_dollop.helpers.read_gpkg import read_gpkg


class Depot(BaseModel):
    """A parcel distribution depot — the physical origin of deliveries."""

    depot_id: int
    zone_id: int
    carrier: str

    @classmethod
    def from_file(cls, path: str | Path, columns: dict[str, str] = {}) -> list[Self]:
        path = Path(path)
        fields = list(cls.model_fields)
        required = list(fields)
        if path.suffix.lower() in (".gpkg", ".shp"):
            records = read_gpkg(path, columns, fields, required)
        else:
            records = read_csv(path, columns, fields, required)
        return [cls(**r) for r in records]
