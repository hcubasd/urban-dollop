import pandas as pd

from urban_dollop.synth.road_capacities import road_capacities


def run():
    pd.DataFrame(road_capacities()).to_csv("road_capacities.csv", index=False)
