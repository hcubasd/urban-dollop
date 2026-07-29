import pandas as pd
import geopandas as gpd
from shapely.geometry import LineString, Point

from urban_dollop.synth.network_loads import network_loads


def _make_inputs():
    network_gdf = gpd.GeoDataFrame(
        [
            {"link_id": 0, "grade": 0.0, "road_type": "road_type_1", "direction": "both",
             "geometry": LineString([(0.0, 0.0), (1.0, 0.0)])},
            {"link_id": 1, "grade": 0.1, "road_type": "road_type_1", "direction": "both",
             "geometry": LineString([(1.0, 0.0), (1.0, 1.0)])},
            {"link_id": 2, "grade": -0.1, "road_type": "road_type_1", "direction": "both",
             "geometry": LineString([(0.0, 0.0), (1.0, 1.0)])},
        ],
        crs=None,
    )

    desire_lines_gdf = gpd.GeoDataFrame(
        [
            {"resource_1_supply": 10, "resource_1_demand": 10,
             "geometry": LineString([(0.0, 0.0), (1.0, 1.0)])},
        ],
        crs=None,
    )

    departures_df = pd.DataFrame([
        {"resource": "resource_1", "time_interval": "interval_1", "probability": 0.6},
        {"resource": "resource_1", "time_interval": "interval_2", "probability": 0.4},
    ])

    time_intervals_df = pd.DataFrame([
        {"time_interval": "interval_1", "duration": 1.0},
        {"time_interval": "interval_2", "duration": 1.0},
    ])

    dwell_times_df = pd.DataFrame([
        {"resource": "resource_1", "dwell_time": 0.5, "load_pct": 0.5},
    ])

    vehicles_df = pd.DataFrame([
        {"vehicle": "vehicle_1", "vehicle_type": "vehicle_type_1",
         "bpr_alpha": 0.15, "bpr_beta": 4.0,
         "time_cost": -1.0, "distance_cost": -0.5, "pcu": 1.0},
    ])

    vehicle_velocities_df = pd.DataFrame([
        {"vehicle": "vehicle_1", "road_type": "road_type_1", "velocity": 1.0},
    ])

    vehicle_capacities_df = pd.DataFrame([
        {"vehicle": "vehicle_1", "resource": "resource_1", "capacity": 3},
    ])

    road_capacities_df = pd.DataFrame([
        {"road_type": "road_type_1", "capacity": 10.0},
    ])

    asc_df = pd.DataFrame([
        {"resource": "resource_1", "vehicle": "vehicle_1", "alpha": 0.0},
    ])

    return (network_gdf, desire_lines_gdf, departures_df, time_intervals_df,
            dwell_times_df, vehicles_df, vehicle_velocities_df,
            vehicle_capacities_df, road_capacities_df, asc_df)


def test_returns_list_of_dicts():
    rows = network_loads(*_make_inputs())
    assert isinstance(rows, list)
    assert all(isinstance(r, dict) for r in rows)


def test_has_required_columns():
    rows = network_loads(*_make_inputs())
    for row in rows:
        assert "link_id" in row
        assert "time_interval" in row
        assert "vehicle" in row
        assert "count" in row
        assert "velocity" in row
        assert "load_pct" in row


def test_count_is_positive():
    rows = network_loads(*_make_inputs())
    for row in rows:
        assert row["count"] > 0.0


def test_velocity_is_positive():
    rows = network_loads(*_make_inputs())
    for row in rows:
        assert row["velocity"] > 0.0


def test_load_pct_in_unit_interval():
    rows = network_loads(*_make_inputs())
    for row in rows:
        assert 0.0 <= row["load_pct"] <= 1.0


def test_time_intervals_are_known():
    rows = network_loads(*_make_inputs())
    valid = {"interval_1", "interval_2"}
    for row in rows:
        assert row["time_interval"] in valid


def test_link_ids_are_valid():
    inputs = _make_inputs()
    rows = network_loads(*inputs)
    n_links = len(inputs[0])
    for row in rows:
        assert 0 <= row["link_id"] < n_links


def test_produces_output_for_nonzero_flows():
    rows = network_loads(*_make_inputs())
    assert len(rows) > 0
