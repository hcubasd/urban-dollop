import os
import sys

import pandas as pd

from urban_dollop.cli._io import check_sigma_relevant
from urban_dollop.synth.copert_v_coefficients import copert_v_coefficients

_KEY_COLUMNS = ("vehicle_type", "pollutant", "gradient_bin", "payload_bin")
_VALUE_COLUMNS = ("alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta", "rf")


def read_copert_v_coefficients(path):
    """(rows, coefficients_complete) if `path` exists, else None -- None
    signals full synthesis. Raises ValueError if the file exists but
    doesn't meet the leaf contract: every key/value column present,
    (vehicle_type, pollutant, gradient_bin, payload_bin) rows distinct,
    and the coefficient columns (alpha through eta, rf) entirely empty or
    entirely populated together -- never a mix, never partially filled.
    """
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path)
    for col in _KEY_COLUMNS + _VALUE_COLUMNS:
        if col not in df.columns:
            raise ValueError(f"{path}: missing '{col}' column")
    keys_seen = list(zip(*(df[col] for col in _KEY_COLUMNS)))
    if len(keys_seen) != len(set(keys_seen)):
        raise ValueError(f"{path}: {_KEY_COLUMNS} rows must be distinct")
    value_frame = df[list(_VALUE_COLUMNS)]
    all_empty = bool(value_frame.isna().all(axis=None))
    all_filled = bool(value_frame.notna().all(axis=None))
    if not all_empty and not all_filled:
        raise ValueError(f"{path}: {_VALUE_COLUMNS} must be entirely empty or entirely populated -- this file already has a mix")
    rows = df[list(_KEY_COLUMNS)].to_dict("records")
    return rows, all_filled


def copert_v_coefficients_need_synthesis(result):
    return result is None or not result[1]


def run(sigma=1.0, sigma_given=False):
    try:
        result = read_copert_v_coefficients("copert_v_coefficients.csv")
        check_sigma_relevant(result, sigma_given, "copert_v_coefficients.csv")
    except ValueError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
    if not copert_v_coefficients_need_synthesis(result):
        return
    rows = result[0] if result is not None else None
    pd.DataFrame(copert_v_coefficients(rows, sigma)).to_csv("copert_v_coefficients.csv", index=False)
