import pandas as pd

from urban_dollop.synth.vehicle_capacities import vehicle_capacities


def run():
    pd.DataFrame(vehicle_capacities()).to_csv("vehicle_capacities.csv", index=False)
