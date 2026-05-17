from urban_dollop.models.base import FileModel


class Depot(FileModel):
    """A parcel distribution depot — the physical origin of deliveries.

    Each carrier operates one or more depots. Parcels are assigned to the
    nearest depot of their carrier by travel time from depot zone to
    destination zone, looked up via zone_id in the skim matrix.

    The depot's exact point coordinates are not used in the simulation;
    zone_id is the spatial reference that connects a depot to the network.
    """

    depot_id: int
    zone_id: int
    carrier: str
