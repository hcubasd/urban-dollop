from pydantic import BaseModel, ConfigDict
from shapely.geometry.base import BaseGeometry


class GeoEntity(BaseModel):
    """Base for domain entities whose geometry is structurally meaningful.

    Reserved for future network entities (links, nodes) where spatial shape
    is part of the domain definition. Zone and Depot do not inherit from
    this — their spatial reference is zone_id, not a coordinate.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    geometry: BaseGeometry
