import os
import sys

import pandas as pd

from urban_dollop.cli._io import check_sigma_relevant
from urban_dollop.synth.dwell_times import dwell_times


def read_dwell_times(path):
    """(resources, values_complete) if `path` exists, else None -- None
    signals full synthesis. Raises ValueError if the file exists but
    doesn't meet the leaf contract: 'resource' present, its values
    distinct, and 'dwell_time'/'load_pct' -- checked jointly, since
    they're synthesized together -- either entirely empty or entirely
    populated (never a mix, and never one column filled while the other
    isn't).
    """
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path)
    for col in ("resource", "dwell_time", "load_pct"):
        if col not in df.columns:
            raise ValueError(f"{path}: missing '{col}' column")
    resources = df["resource"].tolist()
    if len(resources) != len(set(resources)):
        raise ValueError(f"{path}: 'resource' values must be distinct")
    all_empty = bool(df["dwell_time"].isna().all()) and bool(df["load_pct"].isna().all())
    all_filled = bool(df["dwell_time"].notna().all()) and bool(df["load_pct"].notna().all())
    if not all_empty and not all_filled:
        raise ValueError(f"{path}: 'dwell_time'/'load_pct' must be entirely empty or entirely populated -- this file already has a mix")
    return resources, all_filled


def dwell_times_need_synthesis(result):
    return result is None or not result[1]


def run(sigma=1.0, sigma_given=False):
    try:
        result = read_dwell_times("dwell_times.csv")
        check_sigma_relevant(result, sigma_given, "dwell_times.csv")
    except ValueError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
    if not dwell_times_need_synthesis(result):
        return
    resources = result[0] if result is not None else None
    pd.DataFrame(dwell_times(resources, sigma)).to_csv("dwell_times.csv", index=False)
