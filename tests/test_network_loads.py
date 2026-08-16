import math

from shapely.geometry import LineString

from urban_dollop.synth.network_loads import (
    _consolidate,
    _interval_targets,
    _mnl_choice,
    _select_destinations,
    _velocity,
    network_loads,
)


def test_velocity_flips_grade_sign_when_traversed_backward():
    uphill = _velocity(10.0, 6.0, True, 0.15, 4.0, 0.0)
    downhill = _velocity(10.0, 6.0, False, 0.15, 4.0, 0.0)
    assert uphill < 10.0 < downhill
    # the two are exact mirror images of each other around free flow
    assert math.isclose(uphill * downhill, 100.0)


def test_velocity_drops_as_congestion_rises():
    free = _velocity(10.0, 0.0, True, 0.15, 4.0, 0.0)
    congested = _velocity(10.0, 0.0, True, 0.15, 4.0, 2.0)
    assert congested < free


def test_mnl_choice_favours_higher_utility():
    counts = {"a": 0, "b": 0}
    for _ in range(2000):
        counts[_mnl_choice(["a", "b"], [3.0, 0.0])] += 1
    assert counts["a"] > counts["b"] * 3


def test_consolidate_groups_by_origin_agent():
    rows = [
        {"resource": "parcels", "quantity": 2, "origin_agent_id": 1,
         "geometry": LineString([(0, 0), (1, 1)])},
        {"resource": "parcels", "quantity": 3, "origin_agent_id": 1,
         "geometry": LineString([(0, 0), (1, 2)])},
        {"resource": "parcels", "quantity": 5, "origin_agent_id": 1,
         "geometry": LineString([(0, 0), (4, 4)])},
    ]
    shipments = _consolidate(rows)
    assert len(shipments) == 1
    assert sum(d["remaining"] for d in shipments[0]["destinations"]) == 10


def test_consolidate_keeps_resources_separate():
    rows = [
        {"resource": "parcels", "quantity": 2, "origin_agent_id": 1,
         "geometry": LineString([(0, 0), (1, 1)])},
        {"resource": "grains", "quantity": 2, "origin_agent_id": 1,
         "geometry": LineString([(0, 0), (1, 1)])},
    ]
    assert len(_consolidate(rows)) == 2


def test_interval_targets_renormalize_over_defined_intervals_only():
    desire_lines = [
        {"resource": "parcels", "quantity": 100, "origin_agent_id": 1,
         "geometry": LineString([(0, 0), (1, 1)])},
    ]
    departures = [
        {"resource": "parcels", "time_interval": "morning", "probability": 0.25},
        {"resource": "parcels", "time_interval": "evening", "probability": 0.25},
        {"resource": "parcels", "time_interval": "ghost", "probability": 0.5},
    ]
    targets = _interval_targets(desire_lines, departures, ["morning", "evening"])
    # ghost isn't a real interval, so the surviving two split the flow evenly
    assert targets == {("parcels", "morning"): 50, ("parcels", "evening"): 50}


def test_select_destinations_stops_at_the_budget():
    shipment = {"destinations": [{"point": (1, 1), "remaining": 10}, {"point": (2, 2), "remaining": 10}]}
    picks, taken = _select_destinations(shipment, 0, 10, 6)
    assert taken == 6
    # nothing is depleted by selection alone
    assert sum(d["remaining"] for d in shipment["destinations"]) == 20


def test_select_destinations_stops_when_shipment_empties():
    shipment = {"destinations": [{"point": (1, 1), "remaining": 4}]}
    picks, taken = _select_destinations(shipment, 0, 10, 100)
    assert taken == 4


def test_select_destinations_uses_nearest_points_after_the_seed():
    shipment = {
        "destinations": [
            {"point": (0, 0), "remaining": 1},
            {"point": (2, 0), "remaining": 1},
            {"point": (1, 0), "remaining": 1},
        ]
    }
    picks, taken = _select_destinations(shipment, 0, 2, 2)
    assert taken == 2
    assert [destination["point"] for destination, _ in picks] == [(0, 0), (1, 0)]


def _fixture():
    """A two-link corridor: node 0 -- node 1 -- node 2, one depot agent at
    node 0 sending parcels to a zone whose only agent sits at node 2.
    """
    network = [
        {"link_id": 0, "grade": 0.0, "road_type": "road", "oneway": False,
         "geometry": LineString([(0.0, 0.0), (1.0, 0.0)])},
        {"link_id": 1, "grade": 0.0, "road_type": "road", "oneway": False,
         "geometry": LineString([(1.0, 0.0), (2.0, 0.0)])},
    ]
    desire_lines = [
        {"resource": "parcels", "quantity": 4, "origin_agent_id": 1,
         "geometry": LineString([(0.0, 0.0), (2.0, 0.0)])},
    ]
    departures = [{"resource": "parcels", "time_interval": "day", "probability": 1.0}]
    time_intervals = [{"time_interval": "day", "duration": 100.0}]
    dwell_times = [{"resource": "parcels", "dwell_time": 1.0, "load_pct": 0.5}]
    vehicles = [{"vehicle": "van", "vehicle_type": "type_1", "bpr_alpha": 0.15, "bpr_beta": 4.0,
                 "time_coefficient": -1.0, "distance_coefficient": -1.0, "pcu": 1.0}]
    vehicle_velocities = [{"vehicle": "van", "road_type": "road", "velocity": 1.0}]
    vehicle_capacities = [{"vehicle": "van", "resource": "parcels", "capacity": 4}]
    consolidation_radii = [{"vehicle": "van", "resource": "parcels", "radius": 1.0}]
    road_capacities = [{"road_type": "road", "capacity": 10.0}]
    ascs = [{"vehicle": "van", "resource": "parcels", "alternative_specific_constant": 0.0}]
    return (network, desire_lines, departures, time_intervals, dwell_times, vehicles,
            vehicle_velocities, vehicle_capacities, consolidation_radii, road_capacities, ascs)


def test_end_to_end_puts_traffic_on_both_links():
    rows = network_loads(*_fixture())
    assert {row["link_id"] for row in rows} == {0, 1}
    assert all(row["vehicle"] == "van" for row in rows)
    assert all(row["resource"] == "parcels" for row in rows)
    assert all(row["time_interval"] == "day" for row in rows)


def test_outbound_traffic_is_marked_forward():
    # the corridor is laid out start-to-end in the direction of travel
    rows = network_loads(*_fixture())
    assert all(row["forward"] is True for row in rows)


def test_return_trip_is_marked_backward():
    fixture = list(_fixture())
    fixture[3] = [{"time_interval": "a", "duration": 100.0}, {"time_interval": "b", "duration": 100.0}]
    fixture[2] = [{"resource": "parcels", "time_interval": "a", "probability": 1.0}]
    rows = network_loads(*fixture)
    outbound = [row for row in rows if row["time_interval"] == "a"]
    returning = [row for row in rows if row["time_interval"] == "b"]
    assert outbound and returning
    assert all(row["forward"] is True for row in outbound)
    assert all(row["forward"] is False for row in returning)


def test_opposing_traffic_in_one_interval_stays_on_separate_rows():
    fixture = list(_fixture())
    # a second shipment running the corridor the other way, so both
    # directions of both links carry traffic in the same interval
    fixture[1] = list(fixture[1]) + [
        {"resource": "parcels", "quantity": 4, "origin_agent_id": 2,
         "geometry": LineString([(2.0, 0.0), (0.0, 0.0)])},
    ]
    rows = network_loads(*fixture)
    keys = [(row["link_id"], row["time_interval"], row["vehicle"], row["forward"]) for row in rows]
    # never merged: each (link, interval, vehicle, direction) appears once
    assert len(keys) == len(set(keys))
    assert {row["forward"] for row in rows} == {True, False}
    # and the both-ways total is still recoverable by summing the pair
    both_ways = sum(row["vehicle_count"] for row in rows if row["link_id"] == 0)
    assert both_ways == 2


def test_a_full_load_fits_one_vehicle():
    rows = network_loads(*_fixture())
    assert all(row["vehicle_count"] == 1 for row in rows)
    assert all(row["load_pct"] == 1.0 for row in rows)


def test_overflowing_capacity_dispatches_more_vehicles():
    fixture = list(_fixture())
    fixture[7] = [{"vehicle": "van", "resource": "parcels", "capacity": 1}]
    rows = network_loads(*fixture)
    assert max(row["vehicle_count"] for row in rows) == 4
    # three full vans and one at the remainder, which here divides evenly
    assert all(row["load_pct"] == 1.0 for row in rows)


def test_partial_last_vehicle_lowers_average_load():
    fixture = list(_fixture())
    fixture[7] = [{"vehicle": "van", "resource": "parcels", "capacity": 3}]
    rows = network_loads(*fixture)
    # 4 units over capacity 3 -> one full van plus one carrying a third
    assert all(row["vehicle_count"] == 2 for row in rows)
    assert all(math.isclose(row["load_pct"], (1.0 + 1 / 3) / 2) for row in rows)


def test_links_without_road_capacity_are_dropped():
    fixture = list(_fixture())
    fixture[9] = [{"road_type": "other", "capacity": 10.0}]
    assert network_loads(*fixture) == []


def test_vehicle_without_velocity_for_the_road_cannot_serve_it():
    fixture = list(_fixture())
    fixture[6] = [{"vehicle": "van", "road_type": "other", "velocity": 1.0}]
    assert network_loads(*fixture) == []


def test_vehicle_without_an_asc_never_bids():
    fixture = list(_fixture())
    fixture[10] = [{"vehicle": "van", "resource": "grains", "alternative_specific_constant": 0.0}]
    assert network_loads(*fixture) == []


def test_departures_naming_unknown_intervals_move_nothing():
    fixture = list(_fixture())
    fixture[2] = [{"resource": "parcels", "time_interval": "ghost", "probability": 1.0}]
    assert network_loads(*fixture) == []


def test_slow_vehicle_is_still_in_transit_when_the_interval_ends():
    fixture = list(_fixture())
    fixture[3] = [{"time_interval": "a", "duration": 0.5}, {"time_interval": "b", "duration": 100.0}]
    fixture[2] = [{"resource": "parcels", "time_interval": "a", "probability": 1.0}]
    rows = network_loads(*fixture)
    # it only reaches the first link in interval a, the second in interval b
    assert {(row["link_id"], row["time_interval"]) for row in rows} == {(0, "a"), (0, "b"), (1, "b")}


def test_return_trip_runs_at_the_dwell_load():
    fixture = list(_fixture())
    fixture[3] = [{"time_interval": "a", "duration": 100.0}, {"time_interval": "b", "duration": 100.0}]
    fixture[2] = [{"resource": "parcels", "time_interval": "a", "probability": 1.0}]
    rows = network_loads(*fixture)
    returning = [row for row in rows if row["time_interval"] == "b"]
    assert returning
    assert all(row["load_pct"] == 0.5 for row in returning)


def test_congestion_slows_the_second_interval():
    fixture = list(_fixture())
    fixture[3] = [{"time_interval": "a", "duration": 100.0}, {"time_interval": "b", "duration": 100.0}]
    fixture[2] = [{"resource": "parcels", "time_interval": "a", "probability": 1.0}]
    fixture[9] = [{"road_type": "road", "capacity": 1.0}]
    rows = network_loads(*fixture)
    outbound = [row for row in rows if row["time_interval"] == "a"]
    returning = [row for row in rows if row["time_interval"] == "b"]
    assert outbound and returning
    assert max(row["velocity"] for row in returning) < min(row["velocity"] for row in outbound)


def test_empty_desire_lines_produce_nothing():
    fixture = list(_fixture())
    fixture[1] = []
    assert network_loads(*fixture) == []
