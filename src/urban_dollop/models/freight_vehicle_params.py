from pathlib import Path
from typing import Self

from pydantic import BaseModel

from urban_dollop.helpers.read_csv import read_csv


class FreightVehicleParams(BaseModel):
    """Cost and capacity parameters for one vehicle type used in freight demand.

    vehicle_id must match the vehicle_id values in vehicles.csv (used by the
    parcel and freight scheduling modules).  capacity_kg determines how many
    trips are needed to move a given shipment weight; cost_per_hour and
    cost_per_km are used in the MNL transport cost calculation.
    """

    vehicle_id: int
    capacity_kg: float
    cost_per_hour: float
    cost_per_km: float

    @classmethod
    def from_file(cls, path: str | Path) -> list[Self]:
        fields = list(cls.model_fields)
        required = [n for n, fi in cls.model_fields.items() if fi.is_required()]
        records = read_csv(Path(path), {}, fields, required)
        return [cls(**r) for r in records]
