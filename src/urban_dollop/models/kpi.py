from pathlib import Path
from typing import Self

from pydantic import BaseModel

from urban_dollop.helpers.read_csv import read_csv
from urban_dollop.helpers.write_csv import write_csv


class KPI(BaseModel):
    indicator: str
    dimension: str
    value: float
    unit: str

    @classmethod
    def from_file(cls, path: str | Path) -> list[Self]:
        records = read_csv(Path(path), {}, list(cls.model_fields))
        return [cls(**r) for r in records]

    @classmethod
    def to_file(cls, kpis: list["KPI"], path: str | Path) -> None:
        write_csv([k.model_dump() for k in kpis], path)
