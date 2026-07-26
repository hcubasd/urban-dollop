import math
import sys

import pandas as pd

from urban_dollop.synth.stratified_resources import stratified_resources


def _validate_slopes(df, filename):
    if "slope" not in df.columns:
        raise ValueError(f"{filename}: missing 'slope' column")
    if not pd.api.types.is_float_dtype(df["slope"]):
        raise ValueError(f"{filename}: 'slope' must be float")
    for col in df.columns:
        if col == "slope":
            continue
        if not pd.api.types.is_string_dtype(df[col]):
            raise ValueError(f"{filename}: stratum column '{col}' must contain strings only")


def _validate_thresholds(df, filename):
    for col in ("resource", "resource_level", "threshold"):
        if col not in df.columns:
            raise ValueError(f"{filename}: missing '{col}' column")
    if not pd.api.types.is_integer_dtype(df["resource_level"]):
        raise ValueError(f"{filename}: 'resource_level' must be integer")
    for resource, group in df.groupby("resource"):
        thresholds = group.sort_values("resource_level")["threshold"].tolist()
        if not pd.isna(thresholds[-1]):
            raise ValueError(f"{filename}: last threshold for '{resource}' must be empty")
        non_null = [v for v in thresholds[:-1] if not pd.isna(v)]
        if non_null != sorted(non_null):
            raise ValueError(f"{filename}: thresholds for '{resource}' must be ascending")


def _normalize(rows):
    return [
        {k: None if isinstance(v, float) and math.isnan(v) else v for k, v in row.items()}
        for row in rows
    ]


def run():
    slopes_df = pd.read_csv("demand_slopes.csv")
    thresholds_df = pd.read_csv("demand_thresholds.csv")
    try:
        _validate_slopes(slopes_df, "demand_slopes.csv")
        _validate_thresholds(thresholds_df, "demand_thresholds.csv")
    except ValueError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
    slopes = slopes_df.to_dict("records")
    thresholds = _normalize(thresholds_df.to_dict("records"))
    pd.DataFrame(stratified_resources(slopes, thresholds)).to_csv("demand.csv", index=False)
