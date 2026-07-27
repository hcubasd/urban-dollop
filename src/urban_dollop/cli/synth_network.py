import warnings

from urban_dollop.synth.network import network


def run():
    gdf = network()
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message=".*CRS.*")
        gdf.to_file("network.gpkg", driver="GPKG")
