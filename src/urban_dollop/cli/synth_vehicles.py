import pandas as pd

from urban_dollop.synth.vehicles import vehicles


def run():
    pd.DataFrame(vehicles()).to_csv("vehicles.csv", index=False)
