from pathlib import Path
from typing import Self

from pydantic import BaseModel, field_validator

from urban_dollop.models.helpers.read_csv import read_csv


class Vehicle(BaseModel):
    """A delivery vehicle type with a parcel capacity constraint.

    Capacity is used by the scheduling module to cluster parcels into
    tours — no tour may carry more parcels than max_parcels.
    """

    vehicle_id: int
    name: str
    max_parcels: int

    @field_validator("max_parcels")
    @classmethod
    def must_be_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError(f"max_parcels must be positive, got {v}")
        return v

    @classmethod
    def from_file(cls, path: str | Path, columns: dict[str, str] = {}) -> list[Self]:
        records = read_csv(path, columns, list(cls.model_fields))
        return [cls(**r) for r in records]
