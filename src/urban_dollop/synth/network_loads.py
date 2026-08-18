import math
from collections import OrderedDict, defaultdict

from scipy.sparse import lil_matrix
from scipy.sparse.csgraph import dijkstra
from scipy.spatial import KDTree

from urban_dollop.helpers.weighted_choice import weighted_choice

_COORD_PRECISION = 10
_MAX_CACHED_PATHS = 32


def _velocity(free_flow, grade, forward, alpha, beta, v_over_c):
    """A vehicle's actual velocity on one link in one direction.

    Grade is stored relative to the link's own start-to-end coordinate
    order, so traversing it backward flips the sign -- the climb becomes
    the descent. That sign flip is the whole reason routes carry a
    direction alongside each link id rather than a bare link id.

    Congestion then scales the grade-adjusted free-flow velocity down by
    the BPR volume-delay factor, 1 + alpha * (v/c)^beta. v/c is a
    property of the link, not of the direction, so both directions share
    it -- only the grade term differs.
    """
    signed_grade = grade if forward else -grade
    effective = free_flow * math.exp(-signed_grade / 100.0)
    if effective <= 0:
        effective = 1e-9
    return effective / (1.0 + alpha * (v_over_c ** beta))


def _mnl_choice(items, utilities):
    """One item drawn with probability exp(u_i) / sum(exp(u)) -- a
    textbook multinomial logit. The max utility is subtracted from every
    exponent first, which cancels out of the ratio exactly but keeps
    exp() from overflowing on large utilities.
    """
    largest = max(utilities)
    return weighted_choice(items, [math.exp(u - largest) for u in utilities])


def _index_nodes(links):
    """Assign a node id to every distinct link endpoint, annotating each
    link with its own two node ids. Returns the node coordinates, indexed
    by node id.
    """
    coord_index = {}
    coords = []
    for link in links:
        for end, key in (("a", "start"), ("b", "end")):
            xy = link[key]
            rounded = (round(xy[0], _COORD_PRECISION), round(xy[1], _COORD_PRECISION))
            if rounded not in coord_index:
                coord_index[rounded] = len(coords)
                coords.append(rounded)
            link[end] = coord_index[rounded]
    return coords


def _vehicle_graph(links, n_nodes, free_flow, alpha, beta, v_over_c):
    """A directed travel-time graph over the links this vehicle can use,
    plus the arc -> (link_id, forward) map needed to turn a node path
    back into a route. A one-way link contributes only its stored
    direction; a two-way link contributes both, at different travel times
    whenever it has any grade at all.
    """
    graph = lil_matrix((n_nodes, n_nodes))
    arcs = {}
    for link in links:
        velocity = free_flow.get(link["road_type"])
        if velocity is None:
            continue
        congestion = v_over_c.get(link["link_id"], 0.0)
        traversals = [(link["a"], link["b"], True)]
        if not link["oneway"]:
            traversals.append((link["b"], link["a"], False))
        for source, target, forward in traversals:
            travel_time = link["length"] / _velocity(velocity, link["grade"], forward, alpha, beta, congestion)
            existing = graph[source, target]
            if existing == 0 or travel_time < existing:
                graph[source, target] = travel_time
                arcs[(source, target)] = (link["link_id"], forward)
    return graph.tocsr(), arcs


def _route(predecessors, source, target, arcs):
    """The (link_id, forward) sequence from source to target, or None if
    the predecessor chain doesn't actually connect them.
    """
    path = []
    node = target
    while node != source:
        previous = predecessors[node]
        if previous < 0:
            return None
        arc = arcs.get((previous, node))
        if arc is None:
            return None
        path.append(arc)
        node = previous
    return list(reversed(path))


def _consolidate(desire_line_rows):
    """Group transactions into depot shipments, keyed by (resource, origin).

    Each transaction retains its destination point and outstanding quantity.
    A dispatched operation starts from one selected destination and bundles
    nearby destinations using its selected vehicle's consolidation radius.
    """
    shipments = {}
    for row in desire_line_rows:
        key = (row["resource"], row["origin_agent_id"])
        coords = list(row["geometry"].coords)
        if key not in shipments:
            shipments[key] = {
                "resource": row["resource"],
                "origin": coords[0],
                "destinations": [],
            }
        shipments[key]["destinations"].append({"point": coords[-1], "remaining": row["quantity"]})
    return list(shipments.values())


def _interval_targets(desire_line_rows, departure_rows, intervals):
    """How many units of each resource depart in each interval.

    A resource's whole transacted flow is spread across the intervals
    departures.csv gives it, renormalized over just the intervals
    time_intervals.csv actually defines -- the two files are synthesized
    independently, so departures may name intervals that don't exist.
    Rounding to whole units happens here: a resource is counted in whole
    units, so a fractional departure isn't a deliverable quantity.
    """
    total_flow = defaultdict(float)
    for row in desire_line_rows:
        total_flow[row["resource"]] += row["quantity"]

    probabilities = defaultdict(dict)
    for row in departure_rows:
        if row["time_interval"] in set(intervals):
            probabilities[row["resource"]][row["time_interval"]] = row["probability"]

    targets = {}
    for resource, by_interval in probabilities.items():
        total_probability = sum(by_interval.values())
        if total_probability <= 0:
            continue
        for interval, probability in by_interval.items():
            share = probability / total_probability
            targets[(resource, interval)] = round(total_flow.get(resource, 0.0) * share)
    return targets


def _select_destinations(shipment, seed_index, radius, budget):
    """Take the seed and its nearest in-radius destinations up to budget."""
    seed = shipment["destinations"][seed_index]
    order = sorted(
        (
            (
                (destination["point"][0] - seed["point"][0]) ** 2
                + (destination["point"][1] - seed["point"][1]) ** 2,
                index,
            )
            for index, destination in enumerate(shipment["destinations"])
            if destination["remaining"] > 0
            and (destination["point"][0] - seed["point"][0]) ** 2
            + (destination["point"][1] - seed["point"][1]) ** 2 <= radius ** 2
        ),
        key=lambda item: (item[0], item[1]),
    )
    picks = []
    taken = 0.0
    for _, index in order:
        if taken >= budget:
            break
        destination = shipment["destinations"][index]
        amount = min(destination["remaining"], budget - taken)
        picks.append((destination, amount))
        taken += amount
    return picks, taken


def _advance(trip, duration, links_by_id, free_flow, vehicle_params, v_over_c):
    """Move a trip forward by one interval's worth of time.

    Returns the (link, direction) pairs it sat on at any point during the
    interval, and whether it arrived. Presence is deliberately binary: a
    vehicle either was on a link during this interval or it wasn't.
    Weighting it by the fraction of the link covered would say a vehicle
    halfway down a link is half a vehicle, which isn't what a link's load
    means -- it's there or it isn't.

    Direction is part of the key, not folded away, because the two
    directions of a graded link are genuinely different traversals: they
    run at different velocities, and downstream emission modelling needs
    the grade's sign, which is only recoverable from the direction.
    """
    alpha, beta = vehicle_params["bpr_alpha"], vehicle_params["bpr_beta"]
    touched = {}
    remaining_time = duration
    while trip["index"] < len(trip["route"]):
        link_id, forward = trip["route"][trip["index"]]
        link = links_by_id[link_id]
        velocity = _velocity(
            free_flow[link["road_type"]], link["grade"], forward, alpha, beta, v_over_c.get(link_id, 0.0)
        )
        touched[(link_id, forward)] = velocity
        needed = (link["length"] - trip["progress"]) / velocity
        if needed > remaining_time:
            trip["progress"] += velocity * remaining_time
            remaining_time = 0.0
            break
        remaining_time -= needed
        trip["index"] += 1
        trip["progress"] = 0.0
    arrived = trip["index"] >= len(trip["route"])
    return touched, arrived, duration - remaining_time


def network_loads(network_rows, desire_line_rows, departure_rows, time_interval_rows,
                  dwell_time_rows, vehicle_rows, vehicle_velocity_rows,
                  vehicle_capacity_rows, consolidation_radius_rows,
                  road_capacity_rows, asc_rows, on_interval=None):
    """One row per (link, time interval, resource, vehicle, direction) the
    simulation put traffic on: link_id, time_interval, resource, vehicle,
    forward, vehicle_count, velocity, load_pct.

    A two-way link travelled both ways in one interval yields two rows,
    not one. Splitting rather than pre-summing keeps the grade's sign
    recoverable downstream (grade is stored relative to the link's own
    start-to-end order, so a backward traversal negates it) and stops two
    genuinely different velocities being averaged into one meaningless
    number. Anything wanting the both-ways total just sums the pair.

    The network is filtered twice before anything moves: links whose road
    type has no road capacity are dropped outright (no capacity, no
    meaningful v/c), and then each vehicle keeps only the links whose road
    type it has a velocity for -- so every vehicle routes on its own
    subgraph, and a vehicle that can't use a road simply never appears on
    it.

    Each interval, every resource departs the share of its total
    transacted flow that departures.csv assigns to that interval. Flow
    leaves as origin/resource shipments (see _consolidate): a weighted draw
    selects an origin and then a seed destination. Vehicles with an ASC,
    capacity, and consolidation radius for that resource bid for the seed
    route. The selected vehicle's radius serves the seed first and then
    nearest in-radius destinations, up to the interval budget; every
    dispatched vehicle drives to the seed. If no vehicle can reach the
    seed, only that seed transaction is discarded.

    Velocities are frozen for the duration of an interval and recomputed
    at the end of it from the loads that interval actually produced, so
    every trip in an interval sees the same congestion and routing decides
    on the state the network was in when the interval opened. Loads do not
    accumulate across intervals: a vehicle that has driven on is no longer
    on the link behind it.
    If on_interval is provided, it receives each interval's completed,
    already-aggregated output rows. This lets callers write those rows and
    discard them while retaining only the state needed by later intervals.
    """
    road_capacity = {row["road_type"]: row["capacity"] for row in road_capacity_rows}
    links = []
    for row in network_rows:
        if row["road_type"] not in road_capacity:
            continue
        coords = list(row["geometry"].coords)
        links.append({
            "link_id": row["link_id"],
            "road_type": row["road_type"],
            "grade": row["grade"],
            "oneway": bool(row["oneway"]),
            "length": row["geometry"].length,
            "start": coords[0],
            "end": coords[-1],
        })
    if not links:
        return []

    node_coords = _index_nodes(links)
    links_by_id = {link["link_id"]: link for link in links}
    kd_tree = KDTree(node_coords)

    vehicles = {row["vehicle"]: row for row in vehicle_rows}
    free_flow = defaultdict(dict)
    for row in vehicle_velocity_rows:
        if row["vehicle"] in vehicles:
            free_flow[row["vehicle"]][row["road_type"]] = row["velocity"]
    capacity = {
        (row["vehicle"], row["resource"]): row["capacity"]
        for row in vehicle_capacity_rows
        if row["vehicle"] in vehicles
    }
    radius = {
        (row["vehicle"], row["resource"]): row["radius"]
        for row in consolidation_radius_rows
        if row["vehicle"] in vehicles and row["radius"] > 0
    }
    asc = {
        (row["vehicle"], row["resource"]): row["alternative_specific_constant"]
        for row in asc_rows
        if row["vehicle"] in vehicles
    }
    dwell = {row["resource"]: (row["dwell_time"], row["load_pct"]) for row in dwell_time_rows}

    intervals = [row["time_interval"] for row in time_interval_rows]
    durations = {row["time_interval"]: row["duration"] for row in time_interval_rows}
    starts = []
    clock = 0.0
    for interval in intervals:
        starts.append(clock)
        clock += durations[interval]

    shipments = _consolidate(desire_line_rows)
    targets = _interval_targets(desire_line_rows, departure_rows, intervals)

    v_over_c = {}
    active = []
    pending_returns = defaultdict(list)
    output = []

    for position, interval in enumerate(intervals):
        duration = durations[interval]
        graphs = {}
        for vehicle, row in vehicles.items():
            usable = [link for link in links if link["road_type"] in free_flow.get(vehicle, {})]
            graphs[vehicle] = _vehicle_graph(
                usable, len(node_coords), free_flow.get(vehicle, {}),
                row["bpr_alpha"], row["bpr_beta"], v_over_c,
            )
        shortest = OrderedDict()

        def paths_from(vehicle, source):
            key = (vehicle, source)
            if key not in shortest:
                graph, _ = graphs[vehicle]
                shortest[key] = dijkstra(
                    graph, directed=True, indices=source, return_predecessors=True
                )
                if len(shortest) > _MAX_CACHED_PATHS:
                    shortest.popitem(last=False)
            else:
                shortest.move_to_end(key)
            return shortest[key]

        for pending in pending_returns.pop(position, []):
            distances, predecessors = paths_from(pending["vehicle"], pending["source"])
            if distances[pending["target"]] == float("inf"):
                continue
            route = _route(predecessors, pending["source"], pending["target"], graphs[pending["vehicle"]][1])
            if route:
                active.append({
                    "vehicle": pending["vehicle"], "route": route, "index": 0, "progress": 0.0,
                    "load_pct": pending["load_pct"], "resource": pending["resource"],
                    "source": pending["source"], "target": pending["target"], "returning": True,
                    "count": pending["count"],
                })

        for resource in sorted({row["resource"] for row in desire_line_rows}):
            budget = targets.get((resource, interval), 0)
            eligible = [
                vehicle for vehicle in vehicles
                if (vehicle, resource) in asc and (vehicle, resource) in capacity and (vehicle, resource) in radius
            ]
            if not eligible:
                continue
            while budget > 0:
                available = [
                    s for s in shipments
                    if s["resource"] == resource and any(d["remaining"] > 0 for d in s["destinations"])
                ]
                if not available:
                    break
                shipment = weighted_choice(
                    available,
                    [sum(d["remaining"] for d in s["destinations"]) for s in available],
                )
                outstanding = [
                    index for index, destination in enumerate(shipment["destinations"])
                    if destination["remaining"] > 0
                ]
                seed_index = weighted_choice(
                    outstanding,
                    [shipment["destinations"][index]["remaining"] for index in outstanding],
                )
                seed = shipment["destinations"][seed_index]

                source = kd_tree.query(shipment["origin"])[1]
                target = kd_tree.query(seed["point"])[1]
                if source == target:
                    picks, taken = _select_destinations(shipment, seed_index, float("inf"), budget)
                    for destination, amount in picks:
                        destination["remaining"] -= amount
                    budget -= taken
                    continue

                options = []
                utilities = []
                for vehicle in eligible:
                    distances, predecessors = paths_from(vehicle, source)
                    if distances[target] == float("inf") or distances[target] <= 0:
                        continue
                    route = _route(predecessors, source, target, graphs[vehicle][1])
                    if not route:
                        continue
                    length = sum(links_by_id[link_id]["length"] for link_id, _ in route)
                    options.append((vehicle, route))
                    utilities.append(
                        asc[(vehicle, resource)]
                        + vehicles[vehicle]["time_coefficient"] * distances[target]
                        + vehicles[vehicle]["distance_coefficient"] * length
                    )

                if not options:
                    seed["remaining"] = 0.0
                    continue

                vehicle, route = _mnl_choice(options, utilities)
                picks, taken = _select_destinations(shipment, seed_index, radius[(vehicle, resource)], budget)
                if taken <= 0:
                    seed["remaining"] = 0.0
                    continue
                per_vehicle = capacity[(vehicle, resource)]
                if per_vehicle <= 0:
                    seed["remaining"] = 0.0
                    continue

                full_count = int(taken // per_vehicle)
                remainder = taken - full_count * per_vehicle
                if full_count:
                    active.append({
                        "vehicle": vehicle, "route": list(route), "index": 0, "progress": 0.0,
                        "load_pct": 1.0, "resource": resource,
                        "source": source, "target": target, "returning": False, "count": full_count,
                    })
                if remainder > 0:
                    active.append({
                        "vehicle": vehicle, "route": list(route), "index": 0, "progress": 0.0,
                        "load_pct": remainder / per_vehicle, "resource": resource,
                        "source": source, "target": target, "returning": False, "count": 1,
                    })

                for destination, amount in picks:
                    destination["remaining"] -= amount
                budget -= taken

        contributions = defaultdict(lambda: {"count": 0, "velocity": 0.0, "load_pct": 0.0})
        still_active = []
        for trip in active:
            touched, arrived, elapsed = _advance(
                trip, duration, links_by_id, free_flow[trip["vehicle"]], vehicles[trip["vehicle"]], v_over_c
            )
            for (link_id, forward), velocity in touched.items():
                entry = contributions[(link_id, forward, trip["resource"], trip["vehicle"])]
                entry["count"] += trip["count"]
                entry["velocity"] += velocity * trip["count"]
                entry["load_pct"] += trip["load_pct"] * trip["count"]

            if not arrived:
                still_active.append(trip)
                continue
            if trip["returning"]:
                continue

            dwell_time, return_load = dwell.get(trip["resource"], (0.0, 0.0))
            ready_at = starts[position] + elapsed + dwell_time
            departs = next((i for i in range(position + 1, len(intervals)) if starts[i] >= ready_at), None)
            if departs is not None:
                pending_returns[departs].append({
                    "vehicle": trip["vehicle"], "source": trip["target"], "target": trip["source"],
                    "load_pct": return_load, "resource": trip["resource"], "count": trip["count"],
                })
        active = still_active

        loads = defaultdict(float)
        interval_output = []
        for (link_id, forward, resource, vehicle), entry in contributions.items():
            loads[link_id] += entry["count"] * vehicles[vehicle]["pcu"]
            interval_output.append({
                "link_id": link_id,
                "time_interval": interval,
                "resource": resource,
                "vehicle": vehicle,
                "forward": forward,
                "vehicle_count": entry["count"],
                "velocity": entry["velocity"] / entry["count"],
                "load_pct": entry["load_pct"] / entry["count"],
            })

        v_over_c = {}
        for link_id, load in loads.items():
            link_capacity = road_capacity[links_by_id[link_id]["road_type"]]
            v_over_c[link_id] = load / link_capacity if link_capacity > 0 else 0.0

        if on_interval is None:
            output.extend(interval_output)
        else:
            on_interval(interval_output)

    return output
