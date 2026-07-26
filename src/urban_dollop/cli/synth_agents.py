import sys
import warnings

import geopandas as gpd
import pandas as pd

from urban_dollop.synth.agents import agents


def _validate(supply_df, demand_df, batch_sizes_df, zones_gdf):
    non_geom_str = [c for c in zones_gdf.columns if c != "geometry" and pd.api.types.is_string_dtype(zones_gdf[c])]
    if len(non_geom_str) != 1:
        raise ValueError(f"zones.gpkg: expected exactly one string non-geometry column, found {len(non_geom_str)}")
    zone_col = non_geom_str[0]

    supply_strata = [c for c in supply_df.columns if pd.api.types.is_string_dtype(supply_df[c])]
    demand_strata = [c for c in demand_df.columns if pd.api.types.is_string_dtype(demand_df[c])]
    if zone_col not in supply_strata:
        raise ValueError(f"zones.gpkg stratum column '{zone_col}' not found in supply.csv")
    if zone_col not in demand_strata:
        raise ValueError(f"zones.gpkg stratum column '{zone_col}' not found in demand.csv")


def run():
    supply_df = pd.read_csv("supply.csv")
    demand_df = pd.read_csv("demand.csv")
    batch_sizes_df = pd.read_csv("batch_sizes.csv")
    zones_gdf = gpd.read_file("zones.gpkg")

    try:
        _validate(supply_df, demand_df, batch_sizes_df, zones_gdf)
    except ValueError as e:
        print(e, file=sys.stderr)
        sys.exit(1)

    gdf = agents(supply_df, demand_df, batch_sizes_df, zones_gdf)

    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message=".*CRS.*")
        gdf.to_file("agents.gpkg", driver="GPKG")
