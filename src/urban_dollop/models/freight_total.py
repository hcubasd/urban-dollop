from pathlib import Path
from typing import Self

from pydantic import BaseModel

from urban_dollop.helpers.read_csv import read_csv


class FreightTotal(BaseModel):
    """Total daily freight demand for one logistic segment.

    tonnes_day is the aggregate weight in tonnes that the synthesizer must
    disaggregate into individual shipments via firm draws and joint MNL.
    """

    logistic_segment: int
    tonnes_day: float

    @classmethod
    def from_file(cls, path: str | Path) -> list[Self]:
        fields = list(cls.model_fields)
        required = [n for n, fi in cls.model_fields.items() if fi.is_required()]
        records = read_csv(Path(path), {}, fields, required)
        return [cls(**r) for r in records]
