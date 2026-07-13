from pathlib import Path
from typing import Self

from pydantic import BaseModel

from urban_dollop.helpers.read_csv import read_csv
from urban_dollop.helpers.write_csv import write_csv


class Firm(BaseModel):
    """A synthetic firm produced by the firm synthesizer.

    Represents a single establishment in the study area. firm_id is
    sequential and 1-based after minimum-employment filtering. Coordinates
    are in the CRS of the zones file used during synthesis.
    """

    firm_id: int
    zone_id: int
    employment_sector: int
    employment: float
    x_coord: float
    y_coord: float

    @classmethod
    def from_file(cls, path: str | Path) -> list[Self]:
        fields = list(cls.model_fields)
        required = [n for n, fi in cls.model_fields.items() if fi.is_required()]
        records = read_csv(Path(path), {}, fields, required)
        return [cls(**r) for r in records]

    @classmethod
    def to_file(cls, firms: list["Firm"], path: str | Path) -> None:
        write_csv([f.model_dump() for f in firms], path)
