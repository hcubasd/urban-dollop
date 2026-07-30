import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import LineString

from urban_dollop.synth.network_emissions import network_emissions


def _make_inputs():
    network_gdf = gpd.GeoDataFrame([
        {"link_id": 0, "grade": 2.0, "road_type": "road_type_1", "direction": "both",
         "geometry": LineString([(0.0, 0.0), (1.0, 0.0)])},
    ], crs=None)

    network_loads_df = pd.DataFrame([
        {"link_id": 0, "time_interval": "interval_1", "vehicle": "vehicle_1",
         "count": 10.0, "velocity": 2.0, "load_pct": 0.5},
    ])

    vehicles_df = pd.DataFrame([
        {"vehicle": "vehicle_1", "vehicle_type": "vehicle_type_1",
         "bpr_alpha": 1.0, "bpr_beta": 1.0, "time_cost": 1.0, "distance_cost": 1.0, "pcu": 1.0},
    ])

    copert_v_df = pd.DataFrame([
        {"vehicle_type": "vehicle_type_1", "pollutant": "pollutant_1",
         "gradient_bin": 2, "payload_bin": 50,
         "alpha": 0.1, "beta": 0.2, "gamma": 0.3, "delta": 0.1,
         "epsilon": 0.05, "zeta": 0.1, "eta": 0.5, "rf": 0.1},
    ])

    emission_factors_df = pd.DataFrame([
        {"vehicle_type": "vehicle_type_1", "pollutant": "pollutant_2", "ef": 0.5},
        {"vehicle_type": "vehicle_type_1", "pollutant": "pollutant_1", "ef": 9.9},
    ])

    return network_loads_df, network_gdf, vehicles_df, copert_v_df, emission_factors_df


def test_returns_list_of_dicts():
    rows = network_emissions(*_make_inputs())
    assert isinstance(rows, list)
    assert all(isinstance(r, dict) for r in rows)


def test_has_required_columns():
    for row in network_emissions(*_make_inputs()):
        for col in ("link_id", "time_interval", "vehicle", "pollutant", "grams"):
            assert col in row


def test_grams_are_non_negative():
    for row in network_emissions(*_make_inputs()):
        assert row["grams"] >= 0.0


def test_copert_v_takes_priority_over_emission_factors():
    rows = network_emissions(*_make_inputs())
    pollutant_1_rows = [r for r in rows if r["pollutant"] == "pollutant_1"]
    # pollutant_1 is in copert_v, so ef=9.9 from emission_factors must not be used
    assert len(pollutant_1_rows) == 1
    link_length = 1.0
    assert pollutant_1_rows[0]["grams"] != 9.9 * link_length * 10.0


def test_emission_factors_used_for_non_copert_pollutants():
    rows = network_emissions(*_make_inputs())
    pollutant_2_rows = [r for r in rows if r["pollutant"] == "pollutant_2"]
    assert len(pollutant_2_rows) == 1
    assert pollutant_2_rows[0]["grams"] == pytest.approx(0.5 * 1.0 * 10.0)


def test_missing_vehicle_type_skipped():
    loads, network, vehicles, copert_v, ef = _make_inputs()
    loads2 = pd.concat([loads, pd.DataFrame([{
        "link_id": 0, "time_interval": "interval_1", "vehicle": "vehicle_99",
        "count": 5.0, "velocity": 1.0, "load_pct": 0.0,
    }])], ignore_index=True)
    rows = network_emissions(loads2, network, vehicles, copert_v, ef)
    assert all(r["vehicle"] != "vehicle_99" for r in rows)
