from pathlib import Path
from typing import Self

from pydantic import BaseModel

from urban_dollop.helpers.read_csv import read_csv


class Microhub(BaseModel):
    """A transshipment point serving zero-emission last-mile delivery.

    Conventional carrier vehicles deliver parcels to the microhub; a
    zero-emission vehicle (cargo bike, e-bike, etc.) completes the last
    mile into the ZEZ. Each microhub is associated with a carrier,
    enabling carrier-specific hub assignment. Loaded from microhubs.csv.
    """

    microhub_id: int
    zone_id: int
    carrier: str

    @classmethod
    def from_file(cls, path: str | Path, columns: dict[str, str] = {}) -> list[Self]:
        records = read_csv(path, columns, list(cls.model_fields))
        return [cls(**r) for r in records]
