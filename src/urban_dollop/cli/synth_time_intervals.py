import pandas as pd

from urban_dollop.synth.time_intervals import time_intervals


def run():
    pd.DataFrame(time_intervals()).to_csv("time_intervals.csv", index=False)
