from urban_dollop.models.base import FileModel


class Depot(FileModel):
    """A parcel distribution depot — the physical origin of deliveries."""

    depot_id: int
    zone_id: int
    carrier: str
