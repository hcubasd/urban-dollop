import os
import sys
import tempfile

import geopandas as gpd
import pandas as pd

from urban_dollop.helpers.require_km import require_km
from urban_dollop.synth.network_loads import network_loads

_REQUIRED = {
    "network.gpkg": ("link_id", "grade", "road_type", "oneway"),
    "desire_lines.gpkg": ("resource", "quantity", "origin_agent_id"),
    "departures.csv": ("resource", "time_interval", "probability"),
    "time_intervals.csv": ("time_interval", "duration"),
    "dwell_times.csv": ("resource", "dwell_time", "load_pct"),
    "vehicles.csv": ("vehicle", "bpr_alpha", "bpr_beta", "time_coefficient", "distance_coefficient", "pcu"),
    "vehicle_velocities.csv": ("vehicle", "road_type", "velocity"),
    "vehicle_capacities.csv": ("vehicle", "resource", "capacity"),
    "consolidation_radii.csv": ("vehicle", "resource", "radius"),
    "road_capacities.csv": ("road_type", "capacity"),
    "alternative_specific_constants.csv": ("vehicle", "resource", "alternative_specific_constant"),
}

_OUTPUT_COLUMNS = [
    "link_id", "time_interval", "resource", "vehicle", "forward", "vehicle_count", "velocity", "load_pct",
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
        # Both network.gpkg and desire_lines.gpkg have their coordinates
        # measured here: a link's own length drives the whole distance/time
        # simulation, and consolidation_radii compares raw point distances
        # between desire-line endpoints. Both need to be genuinely in km,
        # not merely assumed to be -- see require_km's own docstring for why
        # this is a hard requirement rather than a best-effort conversion.
        frames["network.gpkg"] = require_km(frames["network.gpkg"], "network.gpkg")
        frames["desire_lines.gpkg"] = require_km(frames["desire_lines.gpkg"], "desire_lines.gpkg")
    except ValueError as e:
        print(e, file=sys.stderr)
        sys.exit(1)

    rows_by_path = {path: frame.to_dict("records") for path, frame in frames.items()}
    del frames

    descriptor, temporary_path = tempfile.mkstemp(prefix=".network_loads-", suffix=".csv", dir=".")
    os.close(descriptor)
    wrote_rows = False

    def write_interval(rows):
        nonlocal wrote_rows
        if not rows:
            return
        pd.DataFrame(rows, columns=_OUTPUT_COLUMNS).to_csv(
            temporary_path, mode="a", header=not wrote_rows, index=False
        )
        wrote_rows = True

    try:
        network_loads(
            rows_by_path["network.gpkg"],
            rows_by_path["desire_lines.gpkg"],
            rows_by_path["departures.csv"],
            rows_by_path["time_intervals.csv"],
            rows_by_path["dwell_times.csv"],
            rows_by_path["vehicles.csv"],
            rows_by_path["vehicle_velocities.csv"],
            rows_by_path["vehicle_capacities.csv"],
            rows_by_path["consolidation_radii.csv"],
            rows_by_path["road_capacities.csv"],
            rows_by_path["alternative_specific_constants.csv"],
            on_interval=write_interval,
        )
        if not wrote_rows:
            pd.DataFrame(columns=_OUTPUT_COLUMNS).to_csv(temporary_path, index=False)
        os.chmod(temporary_path, 0o644)
        os.replace(temporary_path, "network_loads.csv")
    finally:
        if os.path.exists(temporary_path):
            os.unlink(temporary_path)
