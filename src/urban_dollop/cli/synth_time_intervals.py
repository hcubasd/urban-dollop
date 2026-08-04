import os
import sys

import pandas as pd

from urban_dollop.synth.time_intervals import time_intervals


def run(sigma=1.0, sigma_given=False):
    exists = os.path.exists("time_intervals.csv")
    if exists and sigma_given:
        print("time_intervals.csv: already exists, so --sigma has nothing left to control", file=sys.stderr)
        sys.exit(1)
    if exists:
        return

    pd.DataFrame(time_intervals(sigma)).to_csv("time_intervals.csv", index=False)
