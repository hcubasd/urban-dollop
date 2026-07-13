import pytest

from urban_dollop.models.delivery_trip import DeliveryTrip
from urban_dollop.models.network_link import NetworkLink
from urban_dollop.models.zone_node import ZoneNode
from urban_dollop.network_assignment import assign_network


def make_trip(origin, destination, vehicle_id=1, tour_id=1, trip_id=1):
    return DeliveryTrip(
        tour_id=tour_id,
        trip_id=trip_id,
        carrier="alpha",
        origin_zone_id=origin,
        destination_zone_id=destination,
        n_parcels=10,
        vehicle_id=vehicle_id,
    )


def test_shortest_path_used(network_links, zone_nodes, vehicles):
    # Zone 1→3: shortest is 1→2→3 (25m), not direct 1→3 (50m)
    trips = [make_trip(1, 3)]
    result = assign_network(trips, network_links, zone_nodes, vehicles)

    link_ids = {r.link_id for r in result}
    assert 1 in link_ids  # 1→2
    assert 2 in link_ids  # 2→3
    assert 3 not in link_ids  # direct 1→3 not used


def test_trip_count_accumulates(network_links, zone_nodes, vehicles):
    # Two trips on the same route accumulate n_trips
    trips = [make_trip(1, 3, tour_id=1), make_trip(1, 3, tour_id=2, trip_id=1)]
    result = assign_network(trips, network_links, zone_nodes, vehicles)

    by_link = {r.link_id: r.n_trips for r in result}
    assert by_link[1] == 2
    assert by_link[2] == 2


def test_vehicle_id_preserved(network_links, zone_nodes, vehicles):
    trips = [make_trip(1, 3, vehicle_id=2)]
    result = assign_network(trips, network_links, zone_nodes, vehicles)

    assert all(r.vehicle_id == 2 for r in result)


def test_different_vehicle_types_separate_rows(network_links, zone_nodes, vehicles):
    trips = [make_trip(1, 3, vehicle_id=1), make_trip(1, 3, vehicle_id=2, tour_id=2)]
    result = assign_network(trips, network_links, zone_nodes, vehicles)

    link1_rows = [r for r in result if r.link_id == 1]
    assert len(link1_rows) == 2
    assert {r.vehicle_id for r in link1_rows} == {1, 2}
    assert all(r.n_trips == 1 for r in link1_rows)


def test_same_origin_destination_skipped(network_links, zone_nodes, vehicles):
    trips = [make_trip(1, 1)]
    result = assign_network(trips, network_links, zone_nodes, vehicles)
    assert result == []


def test_empty_trips_returns_empty(network_links, zone_nodes, vehicles):
    result = assign_network([], network_links, zone_nodes, vehicles)
    assert result == []


def test_empty_links_returns_empty(zone_nodes, vehicles):
    trips = [make_trip(1, 3)]
    result = assign_network(trips, [], zone_nodes, vehicles)
    assert result == []


def test_missing_zone_node_raises(network_links, vehicles):
    zone_nodes = [ZoneNode(zone_id=1, node_id=1)]  # zone 3 missing
    trips = [make_trip(1, 3)]
    with pytest.raises(ValueError, match="zone_nodes"):
        assign_network(trips, network_links, zone_nodes, vehicles)


def test_missing_vehicle_id_raises(network_links, zone_nodes, vehicles):
    trips = [make_trip(1, 3, vehicle_id=99)]
    with pytest.raises(ValueError, match="Vehicle IDs"):
        assign_network(trips, network_links, zone_nodes, vehicles)


def test_multi_hop_route(network_links, zone_nodes, vehicles):
    # Zone 1→4: shortest is 1→2→3→4 (10+15+8=33m) vs 1→2→4 (10+30=40m)
    trips = [make_trip(1, 4)]
    result = assign_network(trips, network_links, zone_nodes, vehicles)

    link_ids = {r.link_id for r in result}
    assert link_ids == {1, 2, 4}  # links 1→2, 2→3, 3→4


def test_without_departure_hour_loaded_link_hour_is_none(network_links, zone_nodes, vehicles):
    trips = [make_trip(1, 3)]
    result = assign_network(trips, network_links, zone_nodes, vehicles)
    assert all(r.hour is None for r in result)


def test_departure_hour_disaggregates_by_hour(network_links, zone_nodes, vehicles):
    trip_h6 = DeliveryTrip(
        tour_id=1, trip_id=1, carrier="alpha",
        origin_zone_id=1, destination_zone_id=3,
        n_parcels=5, vehicle_id=1, departure_hour=6,
    )
    trip_h8 = DeliveryTrip(
        tour_id=2, trip_id=1, carrier="alpha",
        origin_zone_id=1, destination_zone_id=3,
        n_parcels=5, vehicle_id=1, departure_hour=8,
    )
    result = assign_network([trip_h6, trip_h8], network_links, zone_nodes, vehicles)

    link1_rows = [r for r in result if r.link_id == 1]
    assert len(link1_rows) == 2
    assert {r.hour for r in link1_rows} == {6, 8}
    assert all(r.n_trips == 1 for r in link1_rows)


def test_parallel_links_uses_shorter(zone_nodes, vehicles):
    # Two directed links between the same node pair; the shorter should win.
    # Summing their distances (the pre-fix bug) would give 5+100=105 m.
    parallel_links = [
        NetworkLink(link_id=10, from_node_id=1, to_node_id=2, distance_m=5.0, road_type="urban"),
        NetworkLink(link_id=11, from_node_id=1, to_node_id=2, distance_m=100.0, road_type="urban"),
    ]
    trips = [make_trip(1, 2)]
    result = assign_network(trips, parallel_links, zone_nodes[:2], vehicles)
    assert len(result) == 1
    assert result[0].link_id == 10
    assert result[0].n_trips == 1


def test_same_hour_trips_accumulate(network_links, zone_nodes, vehicles):
    trips = [
        DeliveryTrip(
            tour_id=i, trip_id=1, carrier="alpha",
            origin_zone_id=1, destination_zone_id=3,
            n_parcels=5, vehicle_id=1, departure_hour=7,
        )
        for i in range(1, 4)
    ]
    result = assign_network(trips, network_links, zone_nodes, vehicles)

    link1 = next(r for r in result if r.link_id == 1)
    assert link1.hour == 7
    assert link1.n_trips == 3
