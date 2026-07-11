from pathlib import Path
from typing import Self

import geopandas as gpd
from pydantic import BaseModel

from urban_dollop.helpers.read_csv import read_csv


class NetworkLink(BaseModel):
    link_id: int
    from_node_id: int
    to_node_id: int
    distance_m: float
    road_type: str
    grade_pct: float = 0.0

    @classmethod
    def from_file(cls, path: str | Path, columns: dict[str, str] = {}) -> list[Self]:
        path = Path(path)
        fields = list(cls.model_fields)
        required = [n for n, fi in cls.model_fields.items() if fi.is_required()]

        if path.suffix.lower() in (".gpkg", ".shp"):
            df = gpd.read_file(path)
            df = df.rename(columns={v: k for k, v in columns.items()})
            if "distance_m" not in df.columns:
                df["distance_m"] = df.geometry.length
            non_dist_required = [f for f in required if f != "distance_m"]
            missing = set(non_dist_required) - set(df.columns)
            if missing:
                raise ValueError(
                    f"Missing columns {missing} in {path}. "
                    "Use columns= to map your column names to canonical names."
                )
            present = [f for f in fields if f in df.columns]
            records = df[present].to_dict("records")
        else:
            records = read_csv(path, columns, fields, required)

        return [cls(**r) for r in records]
