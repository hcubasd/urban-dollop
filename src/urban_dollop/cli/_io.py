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
    resource column, zone_id present among stratum values (which, given
    CSV's homogeneous column typing, already guarantees 'stratum' is
    string-typed -- no file can contain the literal string "zone_id" in a
    column CSV would otherwise read back as numeric, so a separate dtype
    check on 'stratum' would never independently fire), stratum_value is a
    string for every row except zone_id's (zone_id may be int or string --
    it's the one stratum guaranteed to exist and the one with a natural
    real-world numeric identity; checked per-row rather than per-column,
    since stratum_value mixes every dimension in one shared column and
    CSV's homogeneous typing means a numeric zone_id sharing a file with a
    string-labeled sibling dimension round-trips as a string anyway --
    only a per-row check catches a numeric non-zone_id value in a file
    where every dimension happens to be numeric), and every resource
    column contains floats only. Deliberately does NOT require resource
    columns to be entirely empty or entirely filled: a stratum genuinely
    may not participate in every resource (a zone that supplies grain may
    not supply parcels at all), so a resource cell can legitimately stay
    empty forever in an otherwise-complete file -- see
    effects_need_synthesis for how that empty-vs-complete distinction gets
    made.
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
    for col in resource_cols:
        if not pd.api.types.is_float_dtype(df[col]):
            raise ValueError(f"{path}: resource column '{col}' must contain floats only")
    records = df.to_dict("records")
    for row in records:
        if row["stratum"] != "zone_id" and not isinstance(row["stratum_value"], str):
            raise ValueError(f"{path}: 'stratum_value' must be a string for stratum '{row['stratum']}' -- only zone_id may be numeric")
    return records


def effects_need_synthesis(rows):
    """True if `rows` is None (file absent) or every resource cell across
    every row is empty -- both mean "nothing has been decided yet,
    synthesize shape and/or values." False means at least one resource
    value is already set, which now means the file is complete: any
    resource cells still empty are permanent -- "this stratum doesn't
    participate in this resource" -- not "pending fill." A leaf command
    has no business inventing or overwriting that; whether to fill
    anything further is not its call to make once any real data exists.
    """
    if rows is None:
        return True
    resource_cols = [c for c in rows[0] if c not in ("stratum", "stratum_value")]
    return all(
        row[col] is None or (isinstance(row[col], float) and row[col] != row[col])
        for row in rows
        for col in resource_cols
    )


def read_thresholds(path):
    """rows (resource/resource_level/threshold) if `path` exists, else None.
    Raises ValueError if the file exists but doesn't meet the leaf contract:
    exactly the required columns, 'resource' contains strings only,
    'resource_level' contains integers only (a resource is always counted
    in whole units -- finer granularity means a smaller unit, not a
    fractional level), and threshold entirely empty.
    """
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path)
    if set(df.columns) != {"resource", "resource_level", "threshold"}:
        raise ValueError(f"{path}: must have exactly 'resource', 'resource_level', 'threshold' columns")
    if not pd.api.types.is_string_dtype(df["resource"]):
        raise ValueError(f"{path}: 'resource' must contain strings only")
    if not pd.api.types.is_integer_dtype(df["resource_level"]):
        raise ValueError(f"{path}: 'resource_level' must contain integers only")
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
