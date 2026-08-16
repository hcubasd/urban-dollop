import os
import sys

import pandas as pd

from urban_dollop.cli._io import check_sigma_relevant
from urban_dollop.synth.consolidation_radii import consolidation_radii


def read_consolidation_radii(path):
    """Return (pairs, complete), or None when the file is absent."""
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path)
    for column in ("vehicle", "resource", "radius"):
        if column not in df.columns:
            raise ValueError(f"{path}: missing '{column}' column")
    pairs_seen = list(zip(df["vehicle"], df["resource"]))
    if len(pairs_seen) != len(set(pairs_seen)):
        raise ValueError(f"{path}: (vehicle, resource) pairs must be distinct")
    if not df["radius"].dropna().gt(0).all():
        raise ValueError(f"{path}: 'radius' must contain positive values only")
    all_empty = bool(df["radius"].isna().all())
    all_filled = bool(df["radius"].notna().all())
    if not all_empty and not all_filled:
        raise ValueError(f"{path}: 'radius' must be entirely empty or entirely populated -- this file already has a mix")
    return df[["vehicle", "resource"]].to_dict("records"), all_filled


def consolidation_radii_need_synthesis(result):
    return result is None or not result[1]


def run(sigma=1.0, sigma_given=False):
    try:
        result = read_consolidation_radii("consolidation_radii.csv")
        check_sigma_relevant(result, sigma_given, "consolidation_radii.csv")
    except ValueError as error:
        print(error, file=sys.stderr)
        sys.exit(1)
    if not consolidation_radii_need_synthesis(result):
        return
    pairs = result[0] if result is not None else None
    pd.DataFrame(consolidation_radii(pairs, sigma)).to_csv("consolidation_radii.csv", index=False)
