import os
import sys
import warnings

import geopandas as gpd

from urban_dollop.cli._io import check_sigma_relevant
from urban_dollop.synth.zones import zones


def read_zones(path):
    """(zone_ids, geometry_complete) if `path` exists, else None -- None
    signals full synthesis. Raises ValueError if the file exists but
    doesn't meet the leaf contract: 'zone_id' column present, zone_id
    values distinct, and geometry either entirely empty or entirely
    populated (never a mix, same "never guess/mix" contract as the
    effects/thresholds files).
    """
    if not os.path.exists(path):
        return None
    gdf = gpd.read_file(path)
    if "zone_id" not in gdf.columns:
        raise ValueError(f"{path}: missing 'zone_id' column")
    zone_ids = gdf["zone_id"].tolist()
    if len(zone_ids) != len(set(zone_ids)):
        raise ValueError(f"{path}: 'zone_id' values must be distinct")
    all_empty = bool(gdf.geometry.isna().all())
    all_filled = bool(gdf.geometry.notna().all())
    if not all_empty and not all_filled:
        raise ValueError(f"{path}: geometry must be entirely empty or entirely populated -- this file already has a mix")
    return zone_ids, all_filled


def zones_need_synthesis(result):
    """True if `result` is None (file absent) or geometry is entirely
    empty (shape-only, zone_id given but no geometry yet) -- both mean
    synthesize. False means geometry already exists: the file is
    complete, nothing left to do.
    """
    return result is None or not result[1]


def run(sigma=1.0, sigma_given=False):
    try:
        result = read_zones("zones.gpkg")
        check_sigma_relevant(result, sigma_given, "zones.gpkg")
    except ValueError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
    if not zones_need_synthesis(result):
        return
    zone_ids = result[0] if result is not None else None
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message=".*CRS.*")
        gdf = zones(zone_ids, sigma)
        gdf.to_file("zones.gpkg", driver="GPKG")
