import os
import sys
import warnings

import geopandas as gpd
import pandas as pd

from urban_dollop.synth.agents import agents


def _read_rows(path):
    if not os.path.exists(path):
        return None
    try:
        return pd.read_csv(path).to_dict("records")
    except pd.errors.EmptyDataError:
        return []


def _is_whole_number(value):
    return pd.isna(value) or float(value).is_integer()


def _validate_resource_columns(rows, resources, path):
    # NaN in a sparse resource column upcasts the whole pandas column to
    # float64 even when every present value is whole -- so this checks
    # actual values, not column dtype, the same reasoning as elsewhere in
    # this arc wherever sparsity and int-only requirements coexist.
    for row in rows:
        for resource in resources:
            if resource in row and not _is_whole_number(row[resource]):
                raise ValueError(f"{path}: resource column '{resource}' must contain whole numbers only")


def _validate_resource_level(rows, path):
    for row in rows:
        if not _is_whole_number(row["resource_level"]):
            raise ValueError(f"{path}: 'resource_level' must contain whole numbers only")


def run(sigma=1.0, sigma_given=False):
    if sigma_given:
        print("agents.gpkg: synth agents combines existing data, it invents nothing -- --sigma has nothing to control", file=sys.stderr)
        sys.exit(1)
    if os.path.exists("agents.gpkg"):
        return

    required = ["supply.csv", "demand.csv", "capacities.csv", "needs.csv", "zones.gpkg"]
    missing = [path for path in required if not os.path.exists(path)]
    if missing:
        print(f"not ready yet -- synthesize first: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)

    supply_rows = _read_rows("supply.csv")
    demand_rows = _read_rows("demand.csv")
    capacities_rows = _read_rows("capacities.csv")
    needs_rows = _read_rows("needs.csv")
    zones_gdf = gpd.read_file("zones.gpkg")

    try:
        _validate_resource_level(capacities_rows, "capacities.csv")
        _validate_resource_level(needs_rows, "needs.csv")
        candidate_resources = {row["resource"] for row in capacities_rows} | {row["resource"] for row in needs_rows}
        _validate_resource_columns(supply_rows, candidate_resources, "supply.csv")
        _validate_resource_columns(demand_rows, candidate_resources, "demand.csv")
    except ValueError as e:
        print(e, file=sys.stderr)
        sys.exit(1)

    rows = agents(supply_rows, demand_rows, capacities_rows, needs_rows, zones_gdf)

    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message=".*CRS.*")
        if rows:
            gdf = gpd.GeoDataFrame(rows, crs=None)
        else:
            gdf = gpd.GeoDataFrame(columns=["agent_id", "geometry"], crs=None)
        gdf.to_file("agents.gpkg", driver="GPKG")
