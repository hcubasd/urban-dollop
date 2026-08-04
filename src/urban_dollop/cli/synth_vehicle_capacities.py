import os
import sys

import pandas as pd

from urban_dollop.cli._io import check_sigma_relevant
from urban_dollop.synth.vehicle_capacities import vehicle_capacities


def _is_whole_number(value):
    return pd.isna(value) or float(value).is_integer()


def read_vehicle_capacities(path):
    """(pairs, capacity_complete) if `path` exists, else None -- None
    signals full synthesis. Raises ValueError if the file exists but
    doesn't meet the leaf contract: 'vehicle'/'resource'/'capacity'
    present, (vehicle, resource) pairs distinct, 'capacity' entirely
    empty or entirely populated (never a mix), and -- whichever it is --
    every non-empty capacity a whole number, since a vehicle carries a
    whole count of a resource, never a fraction of one.
    """
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path)
    for col in ("vehicle", "resource", "capacity"):
        if col not in df.columns:
            raise ValueError(f"{path}: missing '{col}' column")
    pairs_seen = list(zip(df["vehicle"], df["resource"]))
    if len(pairs_seen) != len(set(pairs_seen)):
        raise ValueError(f"{path}: (vehicle, resource) pairs must be distinct")
    if not all(_is_whole_number(v) for v in df["capacity"]):
        raise ValueError(f"{path}: 'capacity' must contain whole numbers only")
    all_empty = bool(df["capacity"].isna().all())
    all_filled = bool(df["capacity"].notna().all())
    if not all_empty and not all_filled:
        raise ValueError(f"{path}: 'capacity' must be entirely empty or entirely populated -- this file already has a mix")
    pairs = df[["vehicle", "resource"]].to_dict("records")
    return pairs, all_filled


def vehicle_capacities_need_synthesis(result):
    return result is None or not result[1]


def run(sigma=1.0, sigma_given=False):
    try:
        result = read_vehicle_capacities("vehicle_capacities.csv")
        check_sigma_relevant(result, sigma_given, "vehicle_capacities.csv")
    except ValueError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
    if not vehicle_capacities_need_synthesis(result):
        return
    pairs = result[0] if result is not None else None
    pd.DataFrame(vehicle_capacities(pairs, sigma)).to_csv("vehicle_capacities.csv", index=False)
