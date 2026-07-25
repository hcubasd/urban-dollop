import pandas as pd

from urban_dollop.synth.resource_thresholds import resource_thresholds


def run():
    headers, rows = resource_thresholds()
    pd.DataFrame(rows, columns=["resource"] + headers).to_csv("supply_thresholds.csv", index=False)
