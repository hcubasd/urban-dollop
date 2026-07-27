import pandas as pd

from urban_dollop.synth.departures import departures


def run():
    pd.DataFrame(departures()).to_csv("departures.csv", index=False)
