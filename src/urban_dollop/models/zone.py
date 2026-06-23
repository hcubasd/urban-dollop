from pathlib import Path
from typing import Self

import geopandas as gpd
from pydantic import BaseModel

from urban_dollop.helpers.read_csv import read_csv
from urban_dollop.helpers.read_gpkg import read_gpkg


class Zone(BaseModel):
    """A traffic analysis zone identified by its integer zone_id.

    x and y hold the zone centroid coordinates (in the CRS of the source
    file) and are populated automatically when loading from a GeoPackage or
    shapefile. They are optional so zones can also be constructed
    programmatically without geometry.
    """

    zone_id: int
    x: float | None = None
    y: float | None = None

    @classmethod
    def from_file(cls, path: str | Path, columns: dict[str, str] = {}) -> list[Self]:
        path = Path(path)
        fields = list(cls.model_fields)
        required = [n for n, fi in cls.model_fields.items() if fi.is_required()]

        if path.suffix.lower() in (".gpkg", ".shp"):
            df = gpd.read_file(path)
            df = df.rename(columns={v: k for k, v in columns.items()})
            geo_fields = {"x", "y"}
            non_geo_required = [f for f in required if f not in geo_fields]
            missing = set(non_geo_required) - set(df.columns)
            if missing:
                raise ValueError(
                    f"Missing columns {missing} in {path}. "
                    "Use columns= to map your column names to canonical names."
                )
            present = [f for f in fields if f in df.columns and f not in geo_fields]
            records = df[present].to_dict("records")
            if "x" in fields and "y" in fields and df.geometry is not None:
                centroids = df.geometry.centroid
                for i, r in enumerate(records):
                    r["x"] = float(centroids.iloc[i].x)
                    r["y"] = float(centroids.iloc[i].y)
        else:
            records = read_csv(path, columns, fields, required)

        return [cls(**r) for r in records]
