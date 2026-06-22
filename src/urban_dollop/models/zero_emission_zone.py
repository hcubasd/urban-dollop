from pathlib import Path
from typing import Self

from pydantic import BaseModel

from urban_dollop.helpers.read_csv import read_csv


class ZeroEmissionZone(BaseModel):
    """A zone that restricts conventional vehicle access.

    Parcels destined for a ZEZ are rerouted through a microhub at the
    zone boundary; the last mile is served by a zero-emission vehicle.
    Loaded from zero_emission_zones.csv.
    """

    zone_id: int

    @classmethod
    def from_file(cls, path: str | Path, columns: dict[str, str] = {}) -> list[Self]:
        records = read_csv(path, columns, list(cls.model_fields))
        return [cls(**r) for r in records]
