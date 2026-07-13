from pathlib import Path
from typing import Self

from pydantic import BaseModel

from urban_dollop.helpers.read_csv import read_csv
from urban_dollop.helpers.write_csv import write_csv


class Shipment(BaseModel):
    """A single freight shipment produced by the freight demand synthesizer.

    Each record represents one physical shipment moving from origin_zone_id to
    destination_zone_id. The vehicle_id and weight_class reflect the joint
    MNL draw; weight_kg may be smaller than the nominal class weight for the
    last shipment that exhausts a logistic-segment budget.
    """

    shipment_id: int
    origin_zone_id: int
    destination_zone_id: int
    logistic_segment: int
    vehicle_id: int
    weight_kg: float
    weight_class: int

    @classmethod
    def from_file(cls, path: str | Path) -> list[Self]:
        fields = list(cls.model_fields)
        required = [n for n, fi in cls.model_fields.items() if fi.is_required()]
        records = read_csv(Path(path), {}, fields, required)
        return [cls(**r) for r in records]

    @classmethod
    def to_file(cls, shipments: list["Shipment"], path: str | Path) -> None:
        write_csv([s.model_dump() for s in shipments], path)
