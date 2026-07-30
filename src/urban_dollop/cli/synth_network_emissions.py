import sys

import geopandas as gpd
import pandas as pd

from urban_dollop.synth.network_emissions import network_emissions


def run():
    try:
        network_loads_df = pd.read_csv("network_loads.csv")
    except Exception as e:
        print(f"error reading network_loads.csv: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        network_gdf = gpd.read_file("network.gpkg")
    except Exception as e:
        print(f"error reading network.gpkg: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        vehicles_df = pd.read_csv("vehicles.csv")
    except Exception as e:
        print(f"error reading vehicles.csv: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        copert_v_df = pd.read_csv("copert_v_coefficients.csv")
    except Exception as e:
        print(f"error reading copert_v_coefficients.csv: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        emission_factors_df = pd.read_csv("emission_factors.csv")
    except Exception as e:
        print(f"error reading emission_factors.csv: {e}", file=sys.stderr)
        sys.exit(1)

    rows = network_emissions(network_loads_df, network_gdf, vehicles_df,
                             copert_v_df, emission_factors_df)

    pd.DataFrame(rows).to_csv("network_emissions.csv", index=False)
