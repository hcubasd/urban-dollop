from pathlib import Path
from typing import Self

from pydantic import BaseModel

from urban_dollop.models.helpers.read_csv import read_csv
from urban_dollop.models.helpers.read_gpkg import read_gpkg


class Zone(BaseModel):
    """A traffic analysis zone — the spatial unit of the simulation.

    Zones partition the study area into discrete units. Every parcel has
    an origin zone (the depot's zone) and a destination zone (the delivery
    address zone). Socioeconomic attributes drive demand generation.

    Geometry is not a domain property: spatial reasoning in the simulation
    is done entirely through zone_id indices and the pre-computed skim
    matrix. Zone polygons are only needed for GIS output.
    """

    zone_id: int
    households: int
    employment: int

    @classmethod
    def from_file(cls, path: str | Path, columns: dict[str, str] = {}) -> list[Self]:
        path = Path(path)
        fields = list(cls.model_fields)
        if path.suffix.lower() in (".gpkg", ".shp"):
            records = read_gpkg(path, columns, fields)
        else:
            records = read_csv(path, columns, fields)
        return [cls(**r) for r in records]
