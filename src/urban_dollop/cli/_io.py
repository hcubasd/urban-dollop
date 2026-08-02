import os

import pandas as pd

# Shared by the effects/thresholds CLI wrappers: read-validate-convert on the
# way in, write on the way out. None of the actual synthesis logic lives
# here -- this is strictly the disk boundary.


def read_effects(path):
    """rows (stratum/stratum_value, plus one column per resource) if `path`
    exists, else None -- None signals full synthesis to the matching
    synth/ function. Raises ValueError if the file exists but doesn't meet
    the leaf contract: 'stratum'/'stratum_value' present plus at least one
    resource column, zone_id present among stratum values, stratum_value
    all strings, and every resource column entirely empty (never a mix
    across any resource column or row, and never "already complete" --
    there'd be nothing left for this command to do).
    """
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path)
    for col in ("stratum", "stratum_value"):
        if col not in df.columns:
            raise ValueError(f"{path}: missing '{col}' column")
    resource_cols = [c for c in df.columns if c not in ("stratum", "stratum_value")]
    if not resource_cols:
        raise ValueError(f"{path}: must have at least one resource column")
    if "zone_id" not in set(df["stratum"]):
        raise ValueError(f"{path}: 'zone_id' must be present among stratum values")
    if not pd.api.types.is_string_dtype(df["stratum_value"]):
        raise ValueError(f"{path}: 'stratum_value' must contain strings only")
    if not df[resource_cols].isna().all().all():
        raise ValueError(f"{path}: every resource column must be entirely empty -- this file already has a value in it")
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


def check_sigma_relevant(rows, sigma_given, path):
    """--sigma only ever controls shape invention, which only happens when
    nothing exists yet. If the file already exists (rows is not None) and
    --sigma was explicitly passed, it has nothing left to affect -- raise
    rather than silently ignore it.
    """
    if rows is not None and sigma_given:
        raise ValueError(f"{path}: already exists, so --sigma has nothing left to control")


def write_rows(rows, path):
    pd.DataFrame(rows).to_csv(path, index=False)
