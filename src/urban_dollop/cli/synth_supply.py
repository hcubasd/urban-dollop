import math

import pandas as pd

from urban_dollop.synth.stratified_resources import stratified_resources


def _normalize(rows):
    return [
        {k: None if isinstance(v, float) and math.isnan(v) else v for k, v in row.items()}
        for row in rows
    ]


def run():
    slopes = pd.read_csv("supply_slopes.csv").to_dict("records")
    thresholds = _normalize(pd.read_csv("supply_thresholds.csv").to_dict("records"))
    pd.DataFrame(stratified_resources(slopes, thresholds)).to_csv("supply.csv", index=False)
