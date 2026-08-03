import os
import sys

import pandas as pd

from urban_dollop.cli._io import load_effects_and_thresholds
from urban_dollop.synth.supply import supply


def run(sigma=1.0, sigma_given=False):
    if sigma_given:
        print("supply.csv: synth supply combines existing data, it invents nothing -- --sigma has nothing to control", file=sys.stderr)
        sys.exit(1)
    if os.path.exists("supply.csv"):
        return
    try:
        effects_rows, thresholds_rows = load_effects_and_thresholds("supply_effects.csv", "supply_thresholds.csv")
    except ValueError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
    pd.DataFrame(supply(effects_rows, thresholds_rows)).to_csv("supply.csv", index=False)
