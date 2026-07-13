from pathlib import Path
from typing import Self

from pydantic import BaseModel

from urban_dollop.helpers.read_csv import read_csv


class ShipmentSizeClass(BaseModel):
    """A discrete shipment size alternative in the joint MNL.

    weight_kg is the representative weight used in MNL cost calculations and
    assigned to drawn shipments.  size_class is an integer identifier that
    maps to the ASC_SS_{size_class} parameter in freight_mnl_params.csv.
    """

    logistic_segment: int
    size_class: int
    weight_kg: float

    @classmethod
    def from_file(cls, path: str | Path) -> list[Self]:
        fields = list(cls.model_fields)
        required = [n for n, fi in cls.model_fields.items() if fi.is_required()]
        records = read_csv(Path(path), {}, fields, required)
        return [cls(**r) for r in records]
