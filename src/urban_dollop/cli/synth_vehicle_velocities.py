import pandas as pd

from urban_dollop.synth.vehicle_velocities import vehicle_velocities


def run():
    pd.DataFrame(vehicle_velocities()).to_csv("vehicle_velocities.csv", index=False)
