import os
import sys

import pandas as pd

from urban_dollop.cli._io import check_sigma_relevant
from urban_dollop.synth.road_capacities import road_capacities


def read_road_capacities(path):
    """(road_types, capacity_complete) if `path` exists, else None -- None
    signals full synthesis. Raises ValueError if the file exists but
    doesn't meet the leaf contract: 'road_type' present, its values
    distinct, and 'capacity' entirely empty or entirely populated (never
    a mix).
    """
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path)
    for col in ("road_type", "capacity"):
        if col not in df.columns:
            raise ValueError(f"{path}: missing '{col}' column")
    road_types = df["road_type"].tolist()
    if len(road_types) != len(set(road_types)):
        raise ValueError(f"{path}: 'road_type' values must be distinct")
    all_empty = bool(df["capacity"].isna().all())
    all_filled = bool(df["capacity"].notna().all())
    if not all_empty and not all_filled:
        raise ValueError(f"{path}: 'capacity' must be entirely empty or entirely populated -- this file already has a mix")
    return road_types, all_filled


def road_capacities_need_synthesis(result):
    return result is None or not result[1]


def run(sigma=1.0, sigma_given=False):
    try:
        result = read_road_capacities("road_capacities.csv")
        check_sigma_relevant(result, sigma_given, "road_capacities.csv")
    except ValueError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
    if not road_capacities_need_synthesis(result):
        return
    road_types = result[0] if result is not None else None
    pd.DataFrame(road_capacities(road_types, sigma)).to_csv("road_capacities.csv", index=False)
