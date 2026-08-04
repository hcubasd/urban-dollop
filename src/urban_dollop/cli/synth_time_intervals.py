import os
import sys

import pandas as pd

from urban_dollop.cli._io import check_sigma_relevant
from urban_dollop.synth.time_intervals import time_intervals


def read_time_intervals(path):
    """(labels, duration_complete) if `path` exists, else None -- None
    signals full synthesis. Raises ValueError if the file exists but
    doesn't meet the leaf contract: 'time_interval' present, its values
    distinct, and 'duration' either entirely empty or entirely populated
    (never a mix -- a partially-filled value column has nothing
    well-defined for a leaf command to do with it).
    """
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path)
    for col in ("time_interval", "duration"):
        if col not in df.columns:
            raise ValueError(f"{path}: missing '{col}' column")
    labels = df["time_interval"].tolist()
    if len(labels) != len(set(labels)):
        raise ValueError(f"{path}: 'time_interval' values must be distinct")
    all_empty = bool(df["duration"].isna().all())
    all_filled = bool(df["duration"].notna().all())
    if not all_empty and not all_filled:
        raise ValueError(f"{path}: 'duration' must be entirely empty or entirely populated -- this file already has a mix")
    return labels, all_filled


def time_intervals_need_synthesis(result):
    return result is None or not result[1]


def run(sigma=1.0, sigma_given=False):
    try:
        result = read_time_intervals("time_intervals.csv")
        check_sigma_relevant(result, sigma_given, "time_intervals.csv")
    except ValueError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
    if not time_intervals_need_synthesis(result):
        return
    labels = result[0] if result is not None else None
    pd.DataFrame(time_intervals(labels, sigma)).to_csv("time_intervals.csv", index=False)
