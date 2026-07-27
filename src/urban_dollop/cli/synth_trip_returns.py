import pandas as pd

from urban_dollop.synth.trip_returns import trip_returns


def run():
    pd.DataFrame(trip_returns()).to_csv("trip_returns.csv", index=False)
