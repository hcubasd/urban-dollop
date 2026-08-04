import math

from shapely.geometry import LineString

from urban_dollop.synth.network_emissions import (
    _hot_emission_factor,
    _snap,
    network_emissions,
)


def test_snap_picks_the_nearest_bin():
    assert _snap(1.2, [-6, -4, -2, 0, 2, 4, 6]) == 2
    assert _snap(0.9, [-6, -4, -2, 0, 2, 4, 6]) == 0


def test_snap_clamps_beyond_the_ends():
    assert _snap(-99.0, [-6, -4, -2, 0, 2, 4, 6]) == -6
    assert _snap(99.0, [-6, -4, -2, 0, 2, 4, 6]) == 6


def test_snap_breaks_ties_downward():
    assert _snap(1.0, [0, 2]) == 0


def _coefficients(**overrides):
    row = {
        "alpha": 0.0, "beta": 0.0, "gamma": 6.0, "delta": 0.0,
        "epsilon": 0.0, "zeta": 0.0, "eta": 2.0, "rf": 0.0,
    }
    row.update(overrides)
    return row


def test_hot_emission_factor_evaluates_the_copert_function():
    # constants only: gamma / eta = 6 / 2
    assert _hot_emission_factor(_coefficients(), 10.0) == 3.0


def test_hot_emission_factor_applies_the_reduction_factor():
    assert _hot_emission_factor(_coefficients(rf=0.25), 10.0) == 2.25


def test_hot_emission_factor_is_none_at_zero_velocity():
    # the delta/V term is undefined and a parked vehicle emits no g/km
    assert _hot_emission_factor(_coefficients(), 0.0) is None


def test_hot_emission_factor_is_none_when_the_denominator_vanishes():
    assert _hot_emission_factor(_coefficients(eta=0.0), 10.0) is None


def test_hot_emission_factor_never_goes_negative():
    assert _hot_emission_factor(_coefficients(gamma=-6.0), 10.0) == 0.0


def test_hot_emission_factor_varies_with_velocity():
    coefficients = _coefficients(beta=1.0)
    assert _hot_emission_factor(coefficients, 20.0) > _hot_emission_factor(coefficients, 10.0)


def _fixture():
    """One 2-unit link carrying one van forward at full load."""
    network_loads = [
        {"link_id": 0, "time_interval": "day", "vehicle": "van", "forward": True,
         "vehicle_count": 1, "velocity": 10.0, "load_pct": 1.0},
    ]
    network = [
        {"link_id": 0, "grade": 4.0, "road_type": "road", "oneway": False,
         "geometry": LineString([(0.0, 0.0), (2.0, 0.0)])},
    ]
    vehicles = [{"vehicle": "van", "vehicle_type": "type_1"}]
    copert = [
        dict(vehicle_type="type_1", pollutant="nox", gradient_bin=gradient, payload_bin=payload,
             **_coefficients())
        for gradient in (-6, -4, -2, 0, 2, 4, 6)
        for payload in (0, 50, 100)
    ]
    emission_factors = [{"vehicle_type": "type_1", "pollutant": "pm10", "emission_factor": 0.5}]
    return network_loads, network, vehicles, copert, emission_factors


def test_exhaust_grams_scale_by_distance_travelled():
    rows = network_emissions(*_fixture())
    exhaust = [row for row in rows if row["source"] == "exhaust"]
    assert len(exhaust) == 1
    # factor 3.0 g/km over a 2-unit link, one vehicle
    assert exhaust[0]["grams"] == 6.0
    assert exhaust[0]["pollutant"] == "nox"


def test_non_exhaust_grams_scale_by_the_same_distance():
    rows = network_emissions(*_fixture())
    non_exhaust = [row for row in rows if row["source"] == "non-exhaust"]
    assert len(non_exhaust) == 1
    assert non_exhaust[0]["grams"] == 1.0
    assert non_exhaust[0]["pollutant"] == "pm10"


def test_more_vehicles_emit_proportionally_more():
    fixture = list(_fixture())
    fixture[0] = [dict(fixture[0][0], vehicle_count=3)]
    rows = network_emissions(*fixture)
    assert all(row["grams"] in (18.0, 3.0) for row in rows)


def test_exhaust_and_non_exhaust_are_separate_rows_for_one_pollutant():
    fixture = list(_fixture())
    # the same pollutant produced by both mechanisms
    fixture[4] = [{"vehicle_type": "type_1", "pollutant": "nox", "emission_factor": 0.5}]
    rows = network_emissions(*fixture)
    nox = [row for row in rows if row["pollutant"] == "nox"]
    assert {row["source"] for row in nox} == {"exhaust", "non-exhaust"}
    # never pre-summed: both survive independently, and the total is 6 + 1
    assert sum(row["grams"] for row in nox) == 7.0


def test_backward_traversal_flips_the_grade_before_snapping():
    fixture = list(_fixture())
    # coefficients that differ by gradient bin, so the snap is observable
    fixture[3] = [
        dict(vehicle_type="type_1", pollutant="nox", gradient_bin=gradient, payload_bin=payload,
             **_coefficients(gamma=2.0 * gradient + 20.0))
        for gradient in (-6, -4, -2, 0, 2, 4, 6)
        for payload in (0, 50, 100)
    ]
    forward = network_emissions(*fixture)
    fixture[0] = [dict(fixture[0][0], forward=False)]
    backward = network_emissions(*fixture)
    forward_grams = [row for row in forward if row["source"] == "exhaust"][0]["grams"]
    backward_grams = [row for row in backward if row["source"] == "exhaust"][0]["grams"]
    # the link's stored grade is +4, so forward climbs it and backward
    # descends it -- landing on the +4 and -4 coefficient rows respectively
    assert forward_grams == 28.0
    assert backward_grams == 12.0


def test_load_pct_snaps_onto_the_payload_grid():
    fixture = list(_fixture())
    fixture[3] = [
        dict(vehicle_type="type_1", pollutant="nox", gradient_bin=gradient, payload_bin=payload,
             **_coefficients(gamma=payload / 10.0))
        for gradient in (-6, -4, -2, 0, 2, 4, 6)
        for payload in (0, 50, 100)
    ]
    fixture[0] = [dict(fixture[0][0], load_pct=0.4)]
    rows = network_emissions(*fixture)
    exhaust = [row for row in rows if row["source"] == "exhaust"][0]
    # 40% snaps to the 50 bin: gamma 5.0 / eta 2.0 = 2.5 g/km over 2 units
    assert exhaust["grams"] == 5.0


def test_links_missing_from_the_network_are_skipped():
    fixture = list(_fixture())
    fixture[0] = [dict(fixture[0][0], link_id=99)]
    assert network_emissions(*fixture) == []


def test_vehicles_missing_a_vehicle_type_are_skipped():
    fixture = list(_fixture())
    fixture[2] = [{"vehicle": "truck", "vehicle_type": "type_1"}]
    assert network_emissions(*fixture) == []


def test_a_vehicle_type_with_no_coefficients_emits_no_exhaust():
    fixture = list(_fixture())
    fixture[3] = [
        dict(vehicle_type="other", pollutant="nox", gradient_bin=gradient, payload_bin=payload,
             **_coefficients())
        for gradient in (-6, -4, -2, 0, 2, 4, 6)
        for payload in (0, 50, 100)
    ]
    rows = network_emissions(*fixture)
    assert all(row["source"] == "non-exhaust" for row in rows)


def test_a_vehicle_type_with_no_emission_factor_emits_no_non_exhaust():
    fixture = list(_fixture())
    fixture[4] = [{"vehicle_type": "other", "pollutant": "pm10", "emission_factor": 0.5}]
    rows = network_emissions(*fixture)
    assert all(row["source"] == "exhaust" for row in rows)


def test_a_missing_gradient_payload_combination_is_skipped():
    fixture = list(_fixture())
    # only the 0% payload rows exist, but the load lands on the 100 bin
    fixture[3] = [
        dict(vehicle_type="type_1", pollutant="nox", gradient_bin=gradient, payload_bin=0,
             **_coefficients())
        for gradient in (-6, -4, -2, 0, 2, 4, 6)
    ]
    rows = network_emissions(*fixture)
    assert all(row["source"] == "non-exhaust" for row in rows)


def test_zero_velocity_produces_no_exhaust_but_still_produces_non_exhaust():
    fixture = list(_fixture())
    fixture[0] = [dict(fixture[0][0], velocity=0.0)]
    rows = network_emissions(*fixture)
    assert [row["source"] for row in rows] == ["non-exhaust"]


def test_the_direction_is_carried_through_to_the_output():
    rows = network_emissions(*_fixture())
    assert all(row["forward"] is True for row in rows)
    assert all(row["link_id"] == 0 for row in rows)
    assert all(row["time_interval"] == "day" for row in rows)
    assert all(row["vehicle"] == "van" for row in rows)


def test_empty_loads_produce_nothing():
    fixture = list(_fixture())
    fixture[0] = []
    assert network_emissions(*fixture) == []
