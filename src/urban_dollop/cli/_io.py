import os

import pandas as pd

# Shared by the effects/thresholds CLI wrappers: read-validate-convert on the
# way in, write on the way out. None of the actual synthesis logic lives
# here -- this is strictly the disk boundary.


def read_effects(path):
    """rows (stratum_column/stratum_value/effect) if `path` exists, else
    None -- None signals full synthesis to the matching synth/ function.
    Raises ValueError if the file exists but doesn't meet the leaf contract:
    the required columns, zone_id present among stratum_column values,
    stratum_value all strings, and effect either entirely empty or entirely
    filled (never a mix, and never "already complete" -- there'd be nothing
    left for this command to do).
    """
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path)
    for col in ("stratum_column", "stratum_value", "effect"):
        if col not in df.columns:
            raise ValueError(f"{path}: missing '{col}' column")
    if "zone_id" not in set(df["stratum_column"]):
        raise ValueError(f"{path}: 'zone_id' must be present among stratum_column values")
    if not pd.api.types.is_string_dtype(df["stratum_value"]):
        raise ValueError(f"{path}: 'stratum_value' must contain strings only")
    if not df["effect"].isna().all():
        raise ValueError(f"{path}: 'effect' must be entirely empty -- this file already has a value in it")
    return df.to_dict("records")


def read_thresholds(path):
    """rows (resource/resource_level/threshold) if `path` exists, else None.
    Raises ValueError if the file exists but doesn't meet the leaf contract:
    exactly the required columns, and threshold entirely empty.
    """
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path)
    if set(df.columns) != {"resource", "resource_level", "threshold"}:
        raise ValueError(f"{path}: must have exactly 'resource', 'resource_level', 'threshold' columns")
    if not df["threshold"].isna().all():
        raise ValueError(f"{path}: 'threshold' must be entirely empty -- this file already has a value in it")
    return df.to_dict("records")


def write_rows(rows, path):
    pd.DataFrame(rows).to_csv(path, index=False)
