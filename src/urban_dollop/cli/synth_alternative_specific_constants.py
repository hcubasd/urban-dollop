import os
import sys

import pandas as pd

from urban_dollop.cli._io import check_sigma_relevant
from urban_dollop.synth.alternative_specific_constants import alternative_specific_constants


def read_alternative_specific_constants(path):
    """(pairs, constant_complete) if `path` exists, else None -- None
    signals full synthesis. Raises ValueError if the file exists but
    doesn't meet the leaf contract: 'vehicle'/'resource'/
    'alternative_specific_constant' present, (vehicle, resource) pairs
    distinct, and 'alternative_specific_constant' entirely empty or
    entirely populated (never a mix).
    """
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path)
    for col in ("vehicle", "resource", "alternative_specific_constant"):
        if col not in df.columns:
            raise ValueError(f"{path}: missing '{col}' column")
    pairs_seen = list(zip(df["vehicle"], df["resource"]))
    if len(pairs_seen) != len(set(pairs_seen)):
        raise ValueError(f"{path}: (vehicle, resource) pairs must be distinct")
    all_empty = bool(df["alternative_specific_constant"].isna().all())
    all_filled = bool(df["alternative_specific_constant"].notna().all())
    if not all_empty and not all_filled:
        raise ValueError(f"{path}: 'alternative_specific_constant' must be entirely empty or entirely populated -- this file already has a mix")
    pairs = df[["vehicle", "resource"]].to_dict("records")
    return pairs, all_filled


def alternative_specific_constants_need_synthesis(result):
    return result is None or not result[1]


def run(sigma=1.0, sigma_given=False):
    try:
        result = read_alternative_specific_constants("alternative_specific_constants.csv")
        check_sigma_relevant(result, sigma_given, "alternative_specific_constants.csv")
    except ValueError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
    if not alternative_specific_constants_need_synthesis(result):
        return
    pairs = result[0] if result is not None else None
    pd.DataFrame(alternative_specific_constants(pairs, sigma)).to_csv("alternative_specific_constants.csv", index=False)
