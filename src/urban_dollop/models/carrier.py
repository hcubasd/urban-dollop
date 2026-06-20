from pathlib import Path
from typing import Self

from pydantic import BaseModel, field_validator

from urban_dollop.helpers.read_csv import read_csv


class Carrier(BaseModel):
    """A parcel delivery carrier with a market share fraction.

    Market shares must sum to 1 across all carriers in a scenario.
    The share drives how total zonal demand is split between carriers
    before depot assignment.
    """

    name: str
    share: float

    @field_validator("share")
    @classmethod
    def share_in_unit_interval(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError(f"share must be in [0, 1], got {v}")
        return v

    @classmethod
    def from_file(cls, path: str | Path, columns: dict[str, str] = {}) -> list[Self]:
        records = read_csv(path, columns, list(cls.model_fields))
        return [cls(**r) for r in records]
