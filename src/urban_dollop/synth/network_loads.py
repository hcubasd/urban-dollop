import math
from collections import defaultdict

from scipy.sparse import lil_matrix
from scipy.sparse.csgraph import dijkstra
from scipy.spatial import KDTree

from urban_dollop.helpers.weighted_choice import weighted_choice

_COORD_PRECISION = 10


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
    """Group transactions into depot-to-zone shipments, keyed by
    (resource, origin agent, destination zone).

    This is what stops one package becoming one van trip: every delivery
    the same origin agent owes the same zone for the same resource is one
    shipment, so a vehicle can be filled with deliveries that happen to
    be going the same way. Each underlying transaction stays visible
    inside the shipment as its own destination point and remaining
    quantity, since which specific agents end up on a given run decides
    where that run actually drives.
    """
    shipments = {}
    for row in desire_line_rows:
        key = (row["resource"], row["origin_agent_id"], row["destination_zone_id"])
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


def _select_destinations(shipment, budget):
    """Which of a shipment's destinations ride along on this run, drawn
    weighted by how much each still has outstanding, until either the
    shipment empties or the interval's remaining budget for the resource
    does. Returns the picks and their total, without depleting anything
    -- a run that turns out to be unroutable must leave the shipment
    exactly as it found it.
    """
    outstanding = {
        index: destination["remaining"]
        for index, destination in enumerate(shipment["destinations"])
        if destination["remaining"] > 0
    }
    picks = []
    taken = 0.0
    while taken < budget and outstanding:
        index = weighted_choice(list(outstanding), list(outstanding.values()))
        amount = min(outstanding[index], budget - taken)
        picks.append((shipment["destinations"][index], amount))
        taken += amount
        del outstanding[index]
    return picks, taken


def _centroid(points):
    return (
        sum(x for x, _ in points) / len(points),
        sum(y for _, y in points) / len(points),
    )


def _advance(trip, duration, links_by_id, free_flow, vehicle_params, v_over_c):
    """Move a trip forward by one interval's worth of time.

    Returns the links it sat on at any point during the interval, and
    whether it arrived. Presence is deliberately binary: a vehicle either
    was on a link during this interval or it wasn't. Weighting it by the
    fraction of the link covered would say a vehicle halfway down a link
    is half a vehicle, which isn't what a link's load means -- it's there
    or it isn't.
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
        touched[link_id] = velocity
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
                  vehicle_capacity_rows, road_capacity_rows, asc_rows):
    """One row per (link, time interval, vehicle) the simulation put
    traffic on: link_id, time_interval, vehicle, vehicle_count, velocity,
    load_pct.

    The network is filtered twice before anything moves: links whose road
    type has no road capacity are dropped outright (no capacity, no
    meaningful v/c), and then each vehicle keeps only the links whose road
    type it has a velocity for -- so every vehicle routes on its own
    subgraph, and a vehicle that can't use a road simply never appears on
    it.

    Each interval, every resource departs the share of its total
    transacted flow that departures.csv assigns to that interval. Flow
    leaves as shipments (see _consolidate): a weighted draw picks an
    origin-agent/destination-zone pair, a second weighted draw picks which
    of that pair's destinations ride along, and the run drives to their
    centroid rather than to any one of them. Vehicles that have both an
    ASC and a capacity for the resource bid for the run; those that can
    actually reach the centroid are entered into a multinomial logit on
    asc + time_coefficient * route time + distance_coefficient * route
    distance, and one is drawn. Enough of that vehicle go out to carry the
    flow, the last one part-loaded with whatever's left over. If no vehicle
    can reach the centroid, that origin-agent/destination-zone pair is
    dropped entirely rather than retried against a different draw of
    destinations -- picking a different subset might well succeed, but
    there's no non-arbitrary number of retries, and the pair is already
    looking unreachable.

    Velocities are frozen for the duration of an interval and recomputed
    at the end of it from the loads that interval actually produced, so
    every trip in an interval sees the same congestion and routing decides
    on the state the network was in when the interval opened. Loads do not
    accumulate across intervals: a vehicle that has driven on is no longer
    on the link behind it.
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
        shortest = {}

        def paths_from(vehicle, source):
            if (vehicle, source) not in shortest:
                graph, _ = graphs[vehicle]
                shortest[(vehicle, source)] = dijkstra(
                    graph, directed=True, indices=source, return_predecessors=True
                )
            return shortest[(vehicle, source)]

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
                })

        for resource in sorted({row["resource"] for row in desire_line_rows}):
            budget = targets.get((resource, interval), 0)
            eligible = [v for v in vehicles if (v, resource) in asc and (v, resource) in capacity]
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
                picks, taken = _select_destinations(shipment, budget)
                if taken <= 0:
                    break

                source = kd_tree.query(shipment["origin"])[1]
                target = kd_tree.query(_centroid([d["point"] for d, _ in picks]))[1]
                if source == target:
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
                    for destination in shipment["destinations"]:
                        destination["remaining"] = 0.0
                    continue

                vehicle, route = _mnl_choice(options, utilities)
                per_vehicle = capacity[(vehicle, resource)]
                if per_vehicle <= 0:
                    for destination in shipment["destinations"]:
                        destination["remaining"] = 0.0
                    continue

                dispatched = math.ceil(taken / per_vehicle)
                for unit in range(dispatched):
                    carried = min(per_vehicle, taken - unit * per_vehicle)
                    active.append({
                        "vehicle": vehicle, "route": list(route), "index": 0, "progress": 0.0,
                        "load_pct": carried / per_vehicle, "resource": resource,
                        "source": source, "target": target, "returning": False,
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
            for link_id, velocity in touched.items():
                entry = contributions[(link_id, trip["vehicle"])]
                entry["count"] += 1
                entry["velocity"] += velocity
                entry["load_pct"] += trip["load_pct"]

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
                    "load_pct": return_load, "resource": trip["resource"],
                })
        active = still_active

        loads = defaultdict(float)
        for (link_id, vehicle), entry in contributions.items():
            loads[link_id] += entry["count"] * vehicles[vehicle]["pcu"]
            output.append({
                "link_id": link_id,
                "time_interval": interval,
                "vehicle": vehicle,
                "vehicle_count": entry["count"],
                "velocity": entry["velocity"] / entry["count"],
                "load_pct": entry["load_pct"] / entry["count"],
            })

        v_over_c = {}
        for link_id, load in loads.items():
            link_capacity = road_capacity[links_by_id[link_id]["road_type"]]
            v_over_c[link_id] = load / link_capacity if link_capacity > 0 else 0.0

    return output
