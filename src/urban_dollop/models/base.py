from pathlib import Path
from typing import Self

import geopandas as gpd
import pandas as pd
from pydantic import BaseModel, ConfigDict
from shapely.geometry.base import BaseGeometry

_READERS = {
    ".gpkg": gpd.read_file,
    ".shp": gpd.read_file,
    ".csv": pd.read_csv,
}


class GeoEntity(BaseModel):
    """Base for domain entities whose geometry is structurally meaningful.

    Use this for entities where the spatial shape is part of the domain
    definition (e.g. network links, nodes). Zone and Depot do not inherit
    from this — their spatial reference is zone_id, not a coordinate.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    geometry: BaseGeometry


class FileModel(BaseModel):
    """Mixin that adds from_file() to any model backed by a flat data file."""

    @classmethod
    def from_file(cls, path: str | Path, columns: dict[str, str] = {}) -> list[Self]:
        path = Path(path)
        read = _READERS.get(path.suffix.lower())
        if read is None:
            raise ValueError(
                f"Unsupported file type '{path.suffix}'. Supported: {list(_READERS)}"
            )
        df = read(path)
        df = df.rename(columns={v: k for k, v in columns.items()})
        fields = list(cls.model_fields)
        missing = set(fields) - set(df.columns)
        if missing:
            raise ValueError(
                f"Missing columns {missing} in {path}. "
                "Use columns= to map your column names to canonical names."
            )
        return [cls(**row) for row in df[fields].to_dict("records")]
