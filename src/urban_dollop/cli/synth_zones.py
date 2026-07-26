import warnings

from urban_dollop.synth.zones import zones


def run():
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message=".*CRS.*")
        gdf = zones()
        gdf.to_file("zones.gpkg", driver="GPKG")
