from pathlib import Path
from typing import Self

from pydantic import BaseModel

from urban_dollop.helpers.read_csv import read_csv


class ServiceVehicleShare(BaseModel):
    """Probability that a service trip is made by a given vehicle type.

    vehicle_id must match vehicle_id values in vehicles.csv.  All shares
    must sum to 1.0 across the vehicle fleet.
    """

    vehicle_id: int
    share: float

    @classmethod
    def from_file(cls, path: str | Path) -> list[Self]:
        fields = list(cls.model_fields)
        required = [n for n, fi in cls.model_fields.items() if fi.is_required()]
        records = read_csv(Path(path), {}, fields, required)
        return [cls(**r) for r in records]
