import os
import sys

import pandas as pd

from urban_dollop.synth.departures import departures


def run(sigma=1.0, sigma_given=False):
    exists = os.path.exists("departures.csv")
    if exists and sigma_given:
        print("departures.csv: already exists, so --sigma has nothing left to control", file=sys.stderr)
        sys.exit(1)
    if exists:
        return

    pd.DataFrame(departures(sigma)).to_csv("departures.csv", index=False)
