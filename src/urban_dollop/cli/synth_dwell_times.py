import pandas as pd

from urban_dollop.synth.dwell_times import dwell_times


def run():
    pd.DataFrame(dwell_times()).to_csv("dwell_times.csv", index=False)
