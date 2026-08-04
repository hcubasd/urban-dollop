import os
import sys

import geopandas as gpd
import pandas as pd

from urban_dollop.synth.network_loads import network_loads

_REQUIRED = {
    "network.gpkg": ("link_id", "grade", "road_type", "oneway"),
    "desire_lines.gpkg": ("resource", "quantity", "origin_agent_id", "destination_zone_id"),
    "departures.csv": ("resource", "time_interval", "probability"),
    "time_intervals.csv": ("time_interval", "duration"),
    "dwell_times.csv": ("resource", "dwell_time", "load_pct"),
    "vehicles.csv": ("vehicle", "bpr_alpha", "bpr_beta", "time_coefficient", "distance_coefficient", "pcu"),
    "vehicle_velocities.csv": ("vehicle", "road_type", "velocity"),
    "vehicle_capacities.csv": ("vehicle", "resource", "capacity"),
    "road_capacities.csv": ("road_type", "capacity"),
    "alternative_specific_constants.csv": ("vehicle", "resource", "alternative_specific_constant"),
}

_OUTPUT_COLUMNS = [
    "link_id", "time_interval", "vehicle", "forward", "vehicle_count", "velocity", "load_pct",
]


def _validate(frame, path):
    for column in _REQUIRED[path]:
        if column not in frame.columns:
            raise ValueError(f"{path}: missing '{column}' column")


def run(sigma=1.0, sigma_given=False):
    if sigma_given:
        print(
            "network_loads.csv: synth network-loads combines existing data, it invents nothing -- --sigma has nothing to control",
            file=sys.stderr,
        )
        sys.exit(1)
    if os.path.exists("network_loads.csv"):
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

    rows = network_loads(
        frames["network.gpkg"].to_dict("records"),
        frames["desire_lines.gpkg"].to_dict("records"),
        frames["departures.csv"].to_dict("records"),
        frames["time_intervals.csv"].to_dict("records"),
        frames["dwell_times.csv"].to_dict("records"),
        frames["vehicles.csv"].to_dict("records"),
        frames["vehicle_velocities.csv"].to_dict("records"),
        frames["vehicle_capacities.csv"].to_dict("records"),
        frames["road_capacities.csv"].to_dict("records"),
        frames["alternative_specific_constants.csv"].to_dict("records"),
    )

    pd.DataFrame(rows, columns=_OUTPUT_COLUMNS).to_csv("network_loads.csv", index=False)
