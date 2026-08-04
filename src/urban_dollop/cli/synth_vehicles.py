import os
import sys

import pandas as pd

from urban_dollop.cli._io import check_sigma_relevant
from urban_dollop.synth.vehicles import vehicles

_VALUE_COLUMNS = ("vehicle_type", "bpr_alpha", "bpr_beta", "time_coefficient", "distance_coefficient", "pcu")


def read_vehicles(path):
    """(vehicle_list, values_complete) if `path` exists, else None -- None
    signals full synthesis. Raises ValueError if the file exists but
    doesn't meet the leaf contract: 'vehicle' present, its values
    distinct, and the six value columns -- checked jointly, since they're
    synthesized together -- either entirely empty or entirely populated
    (never a mix, and never some columns filled while others aren't).
    """
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path)
    for col in ("vehicle",) + _VALUE_COLUMNS:
        if col not in df.columns:
            raise ValueError(f"{path}: missing '{col}' column")
    vehicle_list = df["vehicle"].tolist()
    if len(vehicle_list) != len(set(vehicle_list)):
        raise ValueError(f"{path}: 'vehicle' values must be distinct")
    all_empty = all(bool(df[col].isna().all()) for col in _VALUE_COLUMNS)
    all_filled = all(bool(df[col].notna().all()) for col in _VALUE_COLUMNS)
    if not all_empty and not all_filled:
        raise ValueError(f"{path}: {'/'.join(_VALUE_COLUMNS)} must be entirely empty or entirely populated -- this file already has a mix")
    return vehicle_list, all_filled


def vehicles_need_synthesis(result):
    return result is None or not result[1]


def run(sigma=1.0, sigma_given=False):
    try:
        result = read_vehicles("vehicles.csv")
        check_sigma_relevant(result, sigma_given, "vehicles.csv")
    except ValueError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
    if not vehicles_need_synthesis(result):
        return
    vehicle_list = result[0] if result is not None else None
    pd.DataFrame(vehicles(vehicle_list, sigma)).to_csv("vehicles.csv", index=False)
