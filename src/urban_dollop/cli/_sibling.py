import os

import pandas as pd

# Shared by the slopes/thresholds CLI wrappers: reading whatever a sibling
# file in the same pipeline stage already committed to, so a later command
# stays consistent with an earlier one instead of re-randomizing independently.


def _ordered_unique(values):
    seen = []
    for v in values:
        if v not in seen:
            seen.append(v)
    return seen


def borrow_stratum_values(path, stratum_column):
    """Ordered-unique stratum_value entries for one stratum_column in a
    long-format slopes CSV at `path`. None if the file doesn't exist or has
    no rows for that column."""
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path)
    sub = df[df["stratum_column"] == stratum_column]
    values = _ordered_unique(sub["stratum_value"])
    return values or None


def borrow_resources(path):
    """Ordered-unique resource names from a thresholds CSV at `path`.
    None if the file doesn't exist."""
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path)
    return _ordered_unique(df["resource"]) or None
