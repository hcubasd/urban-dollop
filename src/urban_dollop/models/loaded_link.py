from pathlib import Path
from typing import Self

import pandas as pd
from pydantic import BaseModel

from urban_dollop.helpers.read_csv import read_csv


class LoadedLink(BaseModel):
    link_id: int
    vehicle_id: int
    hour: int | None = None
    n_trips: int

    @classmethod
    def from_file(cls, path: str | Path, columns: dict[str, str] = {}) -> list[Self]:
        records = read_csv(path, columns, list(cls.model_fields))
        return [cls(**r) for r in records]

    @classmethod
    def to_file(cls, links: list["LoadedLink"], path: str | Path) -> None:
        pd.DataFrame([l.model_dump() for l in links]).to_csv(path, index=False)
