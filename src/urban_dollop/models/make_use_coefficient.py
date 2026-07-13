from pathlib import Path
from typing import Self

from pydantic import BaseModel

from urban_dollop.helpers.read_csv import read_csv


class MakeUseCoefficient(BaseModel):
    """Production and consumption affinity of an employment sector for a logistic segment.

    make_share and use_share are proportional weights; the synthesizer
    normalises them internally so they need not sum to any particular value
    across sectors.  A value of 0.0 means the sector neither produces nor
    consumes goods in this logistic segment.
    """

    logistic_segment: int
    employment_sector: int
    make_share: float
    use_share: float

    @classmethod
    def from_file(cls, path: str | Path) -> list[Self]:
        fields = list(cls.model_fields)
        required = [n for n, fi in cls.model_fields.items() if fi.is_required()]
        records = read_csv(Path(path), {}, fields, required)
        return [cls(**r) for r in records]
