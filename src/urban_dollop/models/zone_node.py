from pathlib import Path
from typing import Self

from pydantic import BaseModel

from urban_dollop.helpers.read_csv import read_csv


class ZoneNode(BaseModel):
    zone_id: int
    node_id: int

    @classmethod
    def from_file(cls, path: str | Path, columns: dict[str, str] = {}) -> list[Self]:
        fields = ["zone_id", "node_id"]
        records = read_csv(path, columns, fields, fields)
        return [cls(**r) for r in records]
