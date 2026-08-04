import os
import sys

import pandas as pd

from urban_dollop.cli._io import check_sigma_relevant
from urban_dollop.synth.vehicle_velocities import vehicle_velocities


def read_vehicle_velocities(path):
    """(pairs, velocity_complete) if `path` exists, else None -- None
    signals full synthesis. Raises ValueError if the file exists but
    doesn't meet the leaf contract: 'vehicle'/'road_type'/'velocity'
    present, (vehicle, road_type) pairs distinct, and 'velocity' entirely
    empty or entirely populated (never a mix).
    """
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path)
    for col in ("vehicle", "road_type", "velocity"):
        if col not in df.columns:
            raise ValueError(f"{path}: missing '{col}' column")
    pairs_seen = list(zip(df["vehicle"], df["road_type"]))
    if len(pairs_seen) != len(set(pairs_seen)):
        raise ValueError(f"{path}: (vehicle, road_type) pairs must be distinct")
    all_empty = bool(df["velocity"].isna().all())
    all_filled = bool(df["velocity"].notna().all())
    if not all_empty and not all_filled:
        raise ValueError(f"{path}: 'velocity' must be entirely empty or entirely populated -- this file already has a mix")
    pairs = df[["vehicle", "road_type"]].to_dict("records")
    return pairs, all_filled


def vehicle_velocities_need_synthesis(result):
    return result is None or not result[1]


def run(sigma=1.0, sigma_given=False):
    try:
        result = read_vehicle_velocities("vehicle_velocities.csv")
        check_sigma_relevant(result, sigma_given, "vehicle_velocities.csv")
    except ValueError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
    if not vehicle_velocities_need_synthesis(result):
        return
    pairs = result[0] if result is not None else None
    pd.DataFrame(vehicle_velocities(pairs, sigma)).to_csv("vehicle_velocities.csv", index=False)
