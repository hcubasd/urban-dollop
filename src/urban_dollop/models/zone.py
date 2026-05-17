from urban_dollop.models.base import FileModel


class Zone(FileModel):
    """A traffic analysis zone — the spatial unit of the simulation.

    Zones partition the study area into discrete units. Every parcel has
    an origin zone (the depot's zone) and a destination zone (the delivery
    address zone). Socioeconomic attributes drive demand generation.

    Geometry is not a domain property: spatial reasoning in the simulation
    is done entirely through zone_id indices and the pre-computed skim
    matrix. Zone polygons are only needed for GIS output and live in the
    GeoDataFrame layer, not here.
    """

    zone_id: int
    municipality: str
    households: int
    employment: int
