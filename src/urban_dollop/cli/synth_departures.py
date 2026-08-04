import os
import sys

import pandas as pd

from urban_dollop.cli._io import check_sigma_relevant
from urban_dollop.synth.departures import departures


def read_departures(path):
    """(pairs, probability_complete) if `path` exists, else None -- None
    signals full synthesis. Raises ValueError if the file exists but
    doesn't meet the leaf contract: 'resource'/'time_interval'/
    'probability' present, (resource, time_interval) pairs distinct, and
    'probability' entirely empty or entirely populated across the whole
    file (never a mix -- probability is filled per resource-group
    internally, but eligibility to fill anything at all is still a
    file-wide, all-or-nothing check, same as every other leaf command).
    """
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path)
    for col in ("resource", "time_interval", "probability"):
        if col not in df.columns:
            raise ValueError(f"{path}: missing '{col}' column")
    pairs_seen = list(zip(df["resource"], df["time_interval"]))
    if len(pairs_seen) != len(set(pairs_seen)):
        raise ValueError(f"{path}: (resource, time_interval) pairs must be distinct")
    all_empty = bool(df["probability"].isna().all())
    all_filled = bool(df["probability"].notna().all())
    if not all_empty and not all_filled:
        raise ValueError(f"{path}: 'probability' must be entirely empty or entirely populated -- this file already has a mix")
    pairs = df[["resource", "time_interval"]].to_dict("records")
    return pairs, all_filled


def departures_need_synthesis(result):
    return result is None or not result[1]


def run(sigma=1.0, sigma_given=False):
    try:
        result = read_departures("departures.csv")
        check_sigma_relevant(result, sigma_given, "departures.csv")
    except ValueError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
    if not departures_need_synthesis(result):
        return
    pairs = result[0] if result is not None else None
    pd.DataFrame(departures(pairs, sigma)).to_csv("departures.csv", index=False)
