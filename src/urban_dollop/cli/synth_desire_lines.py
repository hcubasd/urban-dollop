import sys
import warnings

import geopandas as gpd
import pandas as pd

from urban_dollop.synth.desire_lines import desire_lines


def _validate(agents_gdf, batch_sizes_df):
    for col in ("resource", "batch_size", "probability"):
        if col not in batch_sizes_df.columns:
            raise ValueError(f"batch_sizes.csv: missing '{col}' column")
    supply_cols = [c for c in agents_gdf.columns if c.endswith("_supply")]
    if not supply_cols:
        raise ValueError("agents.gpkg: no resource supply columns found")


def run():
    agents_gdf = gpd.read_file("agents.gpkg")
    batch_sizes_df = pd.read_csv("batch_sizes.csv")

    try:
        _validate(agents_gdf, batch_sizes_df)
    except ValueError as e:
        print(e, file=sys.stderr)
        sys.exit(1)

    gdf = desire_lines(agents_gdf, batch_sizes_df)

    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message=".*CRS.*")
        gdf.to_file("desire_lines.gpkg", driver="GPKG")
