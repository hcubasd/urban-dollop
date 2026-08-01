import pandas as pd

from urban_dollop.synth.thresholds import random_resources, thresholds


def run(sigma=1.0):
    resources = random_resources(sigma)
    pd.DataFrame(thresholds(resources)).to_csv("supply_thresholds.csv", index=False)
