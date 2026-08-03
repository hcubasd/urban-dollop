import os
import sys

import pandas as pd

from urban_dollop.cli._io import load_effects_and_thresholds
from urban_dollop.synth.needs import needs


def run(sigma=1.0, sigma_given=False):
    if sigma_given:
        print("needs.csv: synth needs combines existing data, it invents nothing -- --sigma has nothing to control", file=sys.stderr)
        sys.exit(1)
    if os.path.exists("needs.csv"):
        return
    try:
        effects_rows, thresholds_rows = load_effects_and_thresholds("need_effects.csv", "need_thresholds.csv")
    except ValueError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
    pd.DataFrame(needs(effects_rows, thresholds_rows)).to_csv("needs.csv", index=False)
