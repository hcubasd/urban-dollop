import os
import sys

import pandas as pd

from urban_dollop.synth.dwell_times import dwell_times


def run(sigma=1.0, sigma_given=False):
    exists = os.path.exists("dwell_times.csv")
    if exists and sigma_given:
        print("dwell_times.csv: already exists, so --sigma has nothing left to control", file=sys.stderr)
        sys.exit(1)
    if exists:
        return

    pd.DataFrame(dwell_times(sigma)).to_csv("dwell_times.csv", index=False)
