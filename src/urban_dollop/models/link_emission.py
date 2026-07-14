from pathlib import Path
from typing import Self

import pandas as pd
from pydantic import BaseModel

from urban_dollop.helpers.read_csv import read_csv


class LinkEmission(BaseModel):
    link_id: int
    vehicle_id: int
    hour: int | None
    pollutant: str
    emission_g: float

    @classmethod
    def from_file(cls, path: str | Path, columns: dict[str, str] = {}) -> list[Self]:
        records = read_csv(Path(path), columns, list(cls.model_fields))
        return [cls(**r) for r in records]

    @classmethod
    def to_file(cls, emissions: list["LinkEmission"], path: str | Path) -> None:
        pd.DataFrame([e.model_dump() for e in emissions]).to_csv(path, index=False)
