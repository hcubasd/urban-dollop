from pathlib import Path
from typing import Self

from pydantic import BaseModel

from urban_dollop.helpers.read_csv import read_csv


class ServiceTripRate(BaseModel):
    """Daily service trip production rate for one employment sector.

    trips_per_employee is the expected number of vehicle trips generated
    per employee per day in this sector.  Values are study-area specific
    and must be calibrated against observed service traffic volumes.
    Sectors with no entry in this file contribute zero trip production.
    """

    employment_sector: int
    trips_per_employee: float

    @classmethod
    def from_file(cls, path: str | Path) -> list[Self]:
        fields = list(cls.model_fields)
        required = [n for n, fi in cls.model_fields.items() if fi.is_required()]
        records = read_csv(Path(path), {}, fields, required)
        return [cls(**r) for r in records]
