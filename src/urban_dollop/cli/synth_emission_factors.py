import os
import sys

import pandas as pd

from urban_dollop.cli._io import check_sigma_relevant
from urban_dollop.synth.emission_factors import emission_factors


def read_emission_factors(path):
    """(pairs, emission_factor_complete) if `path` exists, else None --
    None signals full synthesis. Raises ValueError if the file exists but
    doesn't meet the leaf contract: 'vehicle_type'/'pollutant'/
    'emission_factor' present, (vehicle_type, pollutant) pairs distinct,
    and 'emission_factor' entirely empty or entirely populated (never a
    mix).
    """
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path)
    for col in ("vehicle_type", "pollutant", "emission_factor"):
        if col not in df.columns:
            raise ValueError(f"{path}: missing '{col}' column")
    pairs_seen = list(zip(df["vehicle_type"], df["pollutant"]))
    if len(pairs_seen) != len(set(pairs_seen)):
        raise ValueError(f"{path}: (vehicle_type, pollutant) pairs must be distinct")
    all_empty = bool(df["emission_factor"].isna().all())
    all_filled = bool(df["emission_factor"].notna().all())
    if not all_empty and not all_filled:
        raise ValueError(f"{path}: 'emission_factor' must be entirely empty or entirely populated -- this file already has a mix")
    pairs = df[["vehicle_type", "pollutant"]].to_dict("records")
    return pairs, all_filled


def emission_factors_need_synthesis(result):
    return result is None or not result[1]


def run(sigma=1.0, sigma_given=False):
    try:
        result = read_emission_factors("emission_factors.csv")
        check_sigma_relevant(result, sigma_given, "emission_factors.csv")
    except ValueError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
    if not emission_factors_need_synthesis(result):
        return
    pairs = result[0] if result is not None else None
    pd.DataFrame(emission_factors(pairs, sigma)).to_csv("emission_factors.csv", index=False)
