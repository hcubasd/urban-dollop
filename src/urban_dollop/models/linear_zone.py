from pathlib import Path
from typing import Self

from urban_dollop.helpers.read_csv import read_csv
from urban_dollop.helpers.read_gpkg import read_gpkg
from urban_dollop.models.zone import Zone


class LinearZone(Zone):
    """A zone with the socioeconomic attributes required by the linear demand formulation.

    Required by generate_parcel_demand. Households and employment are available
    from census data in any study area.
    """

    households: float
    employment: float

    @classmethod
    def from_file(cls, path: str | Path, columns: dict[str, str] = {}) -> list[Self]:
        path = Path(path)
        fields = list(cls.model_fields)
        required = [n for n, fi in cls.model_fields.items() if fi.is_required()]
        if path.suffix.lower() in (".gpkg", ".shp"):
            records = read_gpkg(path, columns, fields, required)
        else:
            records = read_csv(path, columns, fields, required)
        return [cls(**r) for r in records]
