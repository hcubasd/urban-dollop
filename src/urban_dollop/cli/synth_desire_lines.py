import os
import sys
import warnings

import geopandas as gpd
import pandas as pd

from urban_dollop.synth.desire_lines import desire_lines


def _is_whole_number(value):
    return pd.isna(value) or float(value).is_integer()


def _resource_names(rows):
    if not rows:
        return set()
    cols = rows[0].keys()
    capacities = {c[: -len("_capacity")] for c in cols if c.endswith("_capacity")}
    needs = {c[: -len("_need")] for c in cols if c.endswith("_need")}
    return capacities & needs


def _validate_zone_id(rows, path):
    if rows and "zone_id" not in rows[0]:
        raise ValueError(f"{path}: missing 'zone_id' column")


def _validate_agents(rows, path):
    # NaN is expected here -- an agent's stratum may not have had a given
    # resource in its Layer 3 intersection at all, which upcasts that
    # resource's columns to float64 for this agent even though every real
    # value is a whole number. Same reasoning as the resource-column check
    # in cli/synth_agents.py.
    for resource in _resource_names(rows):
        for row in rows:
            for suffix in ("_capacity", "_need"):
                if not _is_whole_number(row[f"{resource}{suffix}"]):
                    raise ValueError(f"{path}: '{resource}{suffix}' must contain whole numbers only")


def run(sigma=1.0, sigma_given=False):
    if sigma_given:
        print("desire_lines.gpkg: synth desire-lines combines existing data, it invents nothing -- --sigma has nothing to control", file=sys.stderr)
        sys.exit(1)
    if os.path.exists("desire_lines.gpkg"):
        return
    if not os.path.exists("agents.gpkg"):
        print("agents.gpkg: not ready yet -- synthesize it first", file=sys.stderr)
        sys.exit(1)

    rows = gpd.read_file("agents.gpkg").to_dict("records")
    try:
        _validate_zone_id(rows, "agents.gpkg")
        _validate_agents(rows, "agents.gpkg")
    except ValueError as e:
        print(e, file=sys.stderr)
        sys.exit(1)

    lines = desire_lines(rows)

    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message=".*CRS.*")
        if lines:
            gdf = gpd.GeoDataFrame(lines, crs=None)
        else:
            gdf = gpd.GeoDataFrame(
                columns=["resource", "quantity", "origin_agent_id", "geometry"], crs=None
            )
        gdf.to_file("desire_lines.gpkg", driver="GPKG")
