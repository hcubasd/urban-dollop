from collections import defaultdict

import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra

from urban_dollop.models.delivery_trip import DeliveryTrip
from urban_dollop.models.loaded_link import LoadedLink
from urban_dollop.models.network_link import NetworkLink
from urban_dollop.models.vehicle import Vehicle
from urban_dollop.models.zone_node import ZoneNode
from urban_dollop.network_assignment.config import NetworkAssignmentConfig


def assign_network(
    trips: list[DeliveryTrip],
    links: list[NetworkLink],
    zone_nodes: list[ZoneNode],
    vehicles: list[Vehicle],
    config: NetworkAssignmentConfig | None = None,
) -> list[LoadedLink]:
    """Assign delivery trips to road network links via shortest-path routing.

    For each trip in delivery_trips, finds the shortest-distance path through
    the road network and increments a per-(link, vehicle_type) trip counter.
    Returns one LoadedLink record per (link_id, vehicle_id) pair that carries
    at least one trip.

    Args:
        trips: Trip legs from any upstream scheduler (parcel, freight, service).
        links: Road network links. Directed; distance_m is the edge weight.
        zone_nodes: Maps each zone_id to its network gateway node_id.
        vehicles: Vehicle types (used to validate vehicle_id references).
        config: Optional config; currently unused beyond accepting a seed.

    Returns:
        Sparse list of LoadedLink records, one per (link_id, vehicle_id) with
        n_trips > 0.
    """
    if not links:
        return []
    if not trips:
        return []

    zone_to_node = {zn.zone_id: zn.node_id for zn in zone_nodes}
    vehicle_ids = {v.vehicle_id for v in vehicles}

    _validate_zone_coverage(trips, zone_to_node)
    _validate_vehicle_ids(trips, vehicle_ids)

    node_ids = sorted({l.from_node_id for l in links} | {l.to_node_id for l in links})
    node_index = {n: i for i, n in enumerate(node_ids)}
    n_nodes = len(node_ids)

    rows = [node_index[l.from_node_id] for l in links]
    cols = [node_index[l.to_node_id] for l in links]
    data = [l.distance_m for l in links]
    graph = csr_matrix((data, (rows, cols)), shape=(n_nodes, n_nodes))

    link_lookup: dict[tuple[int, int], NetworkLink] = {
        (node_index[l.from_node_id], node_index[l.to_node_id]): l
        for l in links
    }

    origin_node_indices = sorted({
        node_index[zone_to_node[t.origin_zone_id]]
        for t in trips
    })

    predecessors_by_origin: dict[int, np.ndarray] = {}
    for orig_idx in origin_node_indices:
        _, pred = dijkstra(graph, indices=orig_idx, return_predecessors=True)
        predecessors_by_origin[orig_idx] = pred

    counts: dict[tuple[int, int], int] = defaultdict(int)

    for trip in trips:
        orig_node = zone_to_node[trip.origin_zone_id]
        dest_node = zone_to_node[trip.destination_zone_id]

        if orig_node == dest_node:
            continue

        orig_idx = node_index[orig_node]
        dest_idx = node_index[dest_node]
        pred = predecessors_by_origin[orig_idx]

        route_links = _trace_route(orig_idx, dest_idx, pred, link_lookup)
        for link in route_links:
            counts[(link.link_id, trip.vehicle_id)] += 1

    link_attrs: dict[int, NetworkLink] = {l.link_id: l for l in links}

    return [
        LoadedLink(
            link_id=link_id,
            road_type=link_attrs[link_id].road_type,
            distance_m=link_attrs[link_id].distance_m,
            grade_pct=link_attrs[link_id].grade_pct,
            vehicle_id=vehicle_id,
            n_trips=n_trips,
        )
        for (link_id, vehicle_id), n_trips in sorted(counts.items())
    ]


def _trace_route(
    orig_idx: int,
    dest_idx: int,
    predecessors: np.ndarray,
    link_lookup: dict[tuple[int, int], NetworkLink],
) -> list[NetworkLink]:
    """Reconstruct the sequence of links on the shortest path from orig to dest."""
    if predecessors[dest_idx] < 0:
        return []

    node_sequence: list[int] = []
    current = dest_idx
    while current != orig_idx:
        node_sequence.append(current)
        current = predecessors[current]
        if current < 0:
            return []
    node_sequence.append(orig_idx)
    node_sequence.reverse()

    route = []
    for i in range(len(node_sequence) - 1):
        key = (node_sequence[i], node_sequence[i + 1])
        link = link_lookup.get(key)
        if link is not None:
            route.append(link)
    return route


def _validate_zone_coverage(
    trips: list[DeliveryTrip],
    zone_to_node: dict[int, int],
) -> None:
    missing = {
        z for t in trips
        for z in (t.origin_zone_id, t.destination_zone_id)
        if z not in zone_to_node
    }
    if missing:
        raise ValueError(
            f"Zone IDs {sorted(missing)} appear in trips but have no "
            "entry in zone_nodes. Add a gateway node for each zone."
        )


def _validate_vehicle_ids(
    trips: list[DeliveryTrip],
    vehicle_ids: set[int],
) -> None:
    missing = {t.vehicle_id for t in trips if t.vehicle_id not in vehicle_ids}
    if missing:
        raise ValueError(
            f"Vehicle IDs {sorted(missing)} appear in trips but are "
            "not in the vehicles list."
        )
