from pathlib import Path
from typing import Self

import geopandas as gpd

from urban_dollop.models.base import FileModel
from urban_dollop.models.carrier import Carrier
from urban_dollop.models.zone import Zone


class Depot(FileModel):
    """A parcel distribution depot — the physical origin of deliveries.

    Each carrier operates one or more depots. Parcels are assigned to the
    nearest depot of their carrier by travel time from depot zone to
    destination zone, looked up via the depot's zone in the skim matrix.
    """

    depot_id: int
    zone: Zone
    carrier: Carrier

    @classmethod
    def from_file(
        cls,
        path: str | Path,
        zones: list[Zone],
        carriers: list[Carrier],
        columns: dict[str, str] = {},
    ) -> list[Self]:
        gdf = gpd.read_file(path)
        gdf = gdf.rename(columns={v: k for k, v in columns.items()})
        zone_lookup = {z.zone_id: z for z in zones}
        carrier_lookup = {c.carrier: c for c in carriers}
        depots = []
        for row in gdf[["depot_id", "zone_id", "carrier"]].to_dict("records"):
            zone = zone_lookup.get(row["zone_id"])
            if zone is None:
                raise ValueError(f"Depot {row['depot_id']} references unknown zone_id {row['zone_id']}")
            carrier = carrier_lookup.get(row["carrier"])
            if carrier is None:
                continue  # depot belongs to a carrier not active in this scenario
            depots.append(cls(depot_id=row["depot_id"], zone=zone, carrier=carrier))
        return depots
