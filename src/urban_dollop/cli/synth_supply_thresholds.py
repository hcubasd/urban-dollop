import pandas as pd

from urban_dollop.synth.resource_thresholds import resource_thresholds


def run():
    pd.DataFrame(resource_thresholds()).to_csv("supply_thresholds.csv", index=False)
