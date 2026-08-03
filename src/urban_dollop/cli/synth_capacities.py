import os
import sys

import pandas as pd

from urban_dollop.cli._io import load_effects_and_thresholds
from urban_dollop.synth.capacities import capacities


def run(sigma=1.0, sigma_given=False):
    if sigma_given:
        print("capacities.csv: synth capacities combines existing data, it invents nothing -- --sigma has nothing to control", file=sys.stderr)
        sys.exit(1)
    if os.path.exists("capacities.csv"):
        return
    try:
        effects_rows, thresholds_rows = load_effects_and_thresholds("capacity_effects.csv", "capacity_thresholds.csv")
    except ValueError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
    pd.DataFrame(capacities(effects_rows, thresholds_rows)).to_csv("capacities.csv", index=False)
