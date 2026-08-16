import os
import sys

import geopandas as gpd
import pandas as pd

from urban_dollop.synth.network_emissions import network_emissions

_REQUIRED = {
    "network_loads.csv": ("link_id", "time_interval", "resource", "vehicle", "forward", "vehicle_count", "velocity", "load_pct"),
    "network.gpkg": ("link_id", "grade"),
    "vehicles.csv": ("vehicle", "vehicle_type"),
    "copert_v_coefficients.csv": (
        "vehicle_type", "pollutant", "gradient_bin", "payload_bin",
        "alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta", "rf",
    ),
    "emission_factors.csv": ("vehicle_type", "pollutant", "emission_factor"),
}

_OUTPUT_COLUMNS = [
    "link_id", "time_interval", "resource", "vehicle", "forward", "pollutant", "source", "grams",
]


def _validate(frame, path):
    for column in _REQUIRED[path]:
        if column not in frame.columns:
            raise ValueError(f"{path}: missing '{column}' column")


def run(sigma=1.0, sigma_given=False):
    if sigma_given:
        print(
            "network_emissions.csv: synth network-emissions combines existing data, it invents nothing -- --sigma has nothing to control",
            file=sys.stderr,
        )
        sys.exit(1)
    if os.path.exists("network_emissions.csv"):
        return

    missing = [path for path in _REQUIRED if not os.path.exists(path)]
    if missing:
        print(f"not ready yet -- synthesize first: {', '.join(sorted(missing))}", file=sys.stderr)
        sys.exit(1)

    frames = {}
    for path in _REQUIRED:
        frames[path] = gpd.read_file(path) if path.endswith(".gpkg") else pd.read_csv(path)

    try:
        for path, frame in frames.items():
            _validate(frame, path)
    except ValueError as e:
        print(e, file=sys.stderr)
        sys.exit(1)

    rows = network_emissions(
        frames["network_loads.csv"].to_dict("records"),
        frames["network.gpkg"].to_dict("records"),
        frames["vehicles.csv"].to_dict("records"),
        frames["copert_v_coefficients.csv"].to_dict("records"),
        frames["emission_factors.csv"].to_dict("records"),
    )

    pd.DataFrame(rows, columns=_OUTPUT_COLUMNS).to_csv("network_emissions.csv", index=False)
