from pathlib import Path
from typing import Self

from pydantic import BaseModel

from urban_dollop.helpers.read_csv import read_csv


class ZoneEmployment(BaseModel):
    """Employment by zone and sector — one row per (zone, sector) cell.

    Provides the employment totals that the firm synthesizer draws down when
    populating a synthetic firm register. Each record represents all workers
    in a given sector within a given zone.
    """

    zone_id: int
    employment_sector: int
    employment: float

    @classmethod
    def from_file(cls, path: str | Path, columns: dict[str, str] = {}) -> list[Self]:
        path = Path(path)
        fields = list(cls.model_fields)
        required = [n for n, fi in cls.model_fields.items() if fi.is_required()]
        records = read_csv(path, columns, fields, required)
        return [cls(**r) for r in records]
