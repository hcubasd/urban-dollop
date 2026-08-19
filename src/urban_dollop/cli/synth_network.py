import os
import sys

import geopandas as gpd

from urban_dollop.cli._io import check_sigma_relevant
from urban_dollop.synth.network import network


def read_network(path):
    """(geometries, attributes_complete, crs) if `path` exists, else None --
    None signals full synthesis. Raises ValueError if the file exists but
    doesn't meet the leaf contract: a real CRS set (this file's geometry
    is about to be measured in km by network_loads/network_emissions, and
    there's no way to know it's already in km without one), 'grade'/
    'road_type'/'oneway' present and -- checked jointly, since they're
    synthesized together -- entirely empty or entirely populated (never a
    mix), and geometry entirely populated (there's no legitimate reason
    for topology to be partially given, same reasoning as zones.gpkg).
    link_id is not part of this contract at all -- it's a plain positional
    index, not a real identifier, so it's always reassigned fresh
    regardless of what's given, the same way agent_id is never something a
    caller supplies.
    """
    if not os.path.exists(path):
        return None
    gdf = gpd.read_file(path)
    if gdf.crs is None:
        raise ValueError(
            f"{path}: no CRS set. Every geometry file has to carry a real CRS -- "
            "there's no way to tell a file that's honestly already in km apart from "
            "one that silently isn't, so this is rejected outright rather than guessed at."
        )
    for col in ("grade", "road_type", "oneway"):
        if col not in gdf.columns:
            raise ValueError(f"{path}: missing '{col}' column")
    if not bool(gdf.geometry.notna().all()):
        raise ValueError(f"{path}: 'geometry' must be entirely populated")
    all_empty = bool(gdf["grade"].isna().all()) and bool(gdf["road_type"].isna().all()) and bool(gdf["oneway"].isna().all())
    all_filled = bool(gdf["grade"].notna().all()) and bool(gdf["road_type"].notna().all()) and bool(gdf["oneway"].notna().all())
    if not all_empty and not all_filled:
        raise ValueError(f"{path}: 'grade'/'road_type'/'oneway' must be entirely empty or entirely populated -- this file already has a mix")
    return gdf.geometry.tolist(), all_filled, gdf.crs


def network_need_synthesis(result):
    return result is None or not result[1]


def run(sigma=1.0, sigma_given=False):
    try:
        result = read_network("network.gpkg")
        check_sigma_relevant(result, sigma_given, "network.gpkg")
    except ValueError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
    if not network_need_synthesis(result):
        return
    geometries = result[0] if result is not None else None
    crs = result[2] if result is not None else None
    gdf = network(geometries, sigma, crs=crs)
    gdf.to_file("network.gpkg", driver="GPKG")
