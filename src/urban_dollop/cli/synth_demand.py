import os
import sys

import pandas as pd

from urban_dollop.cli._io import load_effects_and_thresholds
from urban_dollop.synth.demand import demand


def run(sigma=1.0, sigma_given=False):
    if sigma_given:
        print("demand.csv: synth demand combines existing data, it invents nothing -- --sigma has nothing to control", file=sys.stderr)
        sys.exit(1)
    if os.path.exists("demand.csv"):
        return
    try:
        effects_rows, thresholds_rows = load_effects_and_thresholds("demand_effects.csv", "demand_thresholds.csv")
    except ValueError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
    pd.DataFrame(demand(effects_rows, thresholds_rows)).to_csv("demand.csv", index=False)
