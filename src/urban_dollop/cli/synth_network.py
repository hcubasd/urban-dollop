import os
import sys
import warnings

from urban_dollop.synth.network import network


def run(sigma=1.0, sigma_given=False):
    exists = os.path.exists("network.gpkg")
    if exists and sigma_given:
        print("network.gpkg: already exists, so --sigma has nothing left to control", file=sys.stderr)
        sys.exit(1)
    if exists:
        return

    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message=".*CRS.*")
        gdf = network(sigma)
        gdf.to_file("network.gpkg", driver="GPKG")
