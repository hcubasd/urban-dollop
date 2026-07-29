import sys

import geopandas as gpd
import pandas as pd

from urban_dollop.synth.network_loads import network_loads


def run():
    try:
        network_gdf = gpd.read_file("network.gpkg")
    except Exception as e:
        print(f"error reading network.gpkg: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        desire_lines_gdf = gpd.read_file("desire_lines.gpkg")
    except Exception as e:
        print(f"error reading desire_lines.gpkg: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        departures_df = pd.read_csv("departures.csv")
    except Exception as e:
        print(f"error reading departures.csv: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        time_intervals_df = pd.read_csv("time_intervals.csv")
    except Exception as e:
        print(f"error reading time_intervals.csv: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        dwell_times_df = pd.read_csv("dwell_times.csv")
    except Exception as e:
        print(f"error reading dwell_times.csv: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        vehicles_df = pd.read_csv("vehicles.csv")
    except Exception as e:
        print(f"error reading vehicles.csv: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        vehicle_velocities_df = pd.read_csv("vehicle_velocities.csv")
    except Exception as e:
        print(f"error reading vehicle_velocities.csv: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        vehicle_capacities_df = pd.read_csv("vehicle_capacities.csv")
    except Exception as e:
        print(f"error reading vehicle_capacities.csv: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        road_capacities_df = pd.read_csv("road_capacities.csv")
    except Exception as e:
        print(f"error reading road_capacities.csv: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        asc_df = pd.read_csv("alternative_specific_constants.csv")
    except Exception as e:
        print(f"error reading alternative_specific_constants.csv: {e}", file=sys.stderr)
        sys.exit(1)

    for col in ("grade", "road_type", "direction"):
        if col not in network_gdf.columns:
            print(f"network.gpkg missing column: {col}", file=sys.stderr)
            sys.exit(1)

    for col in ("resource", "time_interval", "probability"):
        if col not in departures_df.columns:
            print(f"departures.csv missing column: {col}", file=sys.stderr)
            sys.exit(1)

    for col in ("time_interval", "duration"):
        if col not in time_intervals_df.columns:
            print(f"time_intervals.csv missing column: {col}", file=sys.stderr)
            sys.exit(1)

    dep_intervals = set(departures_df["time_interval"].unique())
    ti_intervals = list(time_intervals_df["time_interval"])
    ti_set = set(ti_intervals)
    if not dep_intervals.issubset(ti_set):
        missing = dep_intervals - ti_set
        print(f"departures.csv references intervals not in time_intervals.csv: {missing}", file=sys.stderr)
        sys.exit(1)

    dep_by_resource = departures_df.groupby("resource")["time_interval"].apply(list)
    for resource, intv_list in dep_by_resource.items():
        intv_order = [ti_intervals.index(i) for i in intv_list]
        if intv_order != sorted(intv_order):
            print(f"departures.csv intervals for resource {resource} are not in time_intervals.csv order",
                  file=sys.stderr)
            sys.exit(1)

    rows = network_loads(
        network_gdf, desire_lines_gdf, departures_df, time_intervals_df,
        dwell_times_df, vehicles_df, vehicle_velocities_df,
        vehicle_capacities_df, road_capacities_df, asc_df,
    )

    pd.DataFrame(rows).to_csv("network_loads.csv", index=False)
