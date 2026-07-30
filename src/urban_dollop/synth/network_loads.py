import math
import random

import geopandas as gpd
import pandas as pd
from scipy.spatial import KDTree
from scipy.sparse import lil_matrix
from scipy.sparse.csgraph import dijkstra
from shapely.geometry import LineString


def _build_graph(network_gdf, vehicle_rows, velocities, road_capacities, link_loads, interval_duration):
    coords_list = []
    coord_index = {}

    def node_id(xy):
        key = (round(xy[0], 10), round(xy[1], 10))
        if key not in coord_index:
            coord_index[key] = len(coords_list)
            coords_list.append(key)
        return coord_index[key]

    edges = []
    for link_id, row in network_gdf.iterrows():
        geom = row.geometry
        c = list(geom.coords)
        a = node_id(c[0])
        b = node_id(c[-1])
        length = geom.length
        road_type = row["road_type"]
        grade = row["grade"]
        direction = row["direction"]
        cap = road_capacities.get(road_type, 1.0)
        pcu_load = link_loads.get(link_id, 0.0)
        v_over_c = pcu_load / cap if cap > 0 else 0.0
        edges.append((link_id, a, b, length, road_type, grade, direction, v_over_c))

    n_nodes = len(coords_list)
    node_coords = list(coords_list)

    vehicle_graphs = {}
    for v_row in vehicle_rows:
        vehicle = v_row["vehicle"]
        alpha = v_row["bpr_alpha"]
        beta = v_row["bpr_beta"]
        g = lil_matrix((n_nodes, n_nodes))
        link_times = {}
        link_lengths = {}
        for link_id, a, b, length, road_type, grade, direction, v_over_c in edges:
            vel = velocities.get((vehicle, road_type), 1.0)
            eff_vel = vel * math.exp(-grade / 100.0)
            if eff_vel <= 0:
                eff_vel = 1e-9
            t0 = length / eff_vel / interval_duration
            bpr = t0 * (1.0 + alpha * (v_over_c ** beta))
            link_times[(vehicle, link_id)] = bpr
            link_lengths[link_id] = length
            if direction in ("both", "forward"):
                existing = g[a, b]
                if existing == 0 or bpr < existing:
                    g[a, b] = bpr
            if direction in ("both", "backward"):
                existing = g[b, a]
                if existing == 0 or bpr < existing:
                    g[b, a] = bpr
        vehicle_graphs[vehicle] = (g.tocsr(), link_times)

    return node_coords, coord_index, edges, vehicle_graphs, link_lengths


def _snap(coord, kd_tree, node_coords):
    _, idx = kd_tree.query(coord)
    return idx


def _route_links(predecessors, dest, src, edges_by_node_pair):
    path = []
    node = dest
    while node != src:
        prev = predecessors[node]
        if prev < 0:
            return None
        link_id = edges_by_node_pair.get((prev, node))
        if link_id is None:
            return None
        path.append(link_id)
        node = prev
    return list(reversed(path))


def network_loads(network_gdf, desire_lines_gdf, departures_df, time_intervals_df,
                  dwell_times_df, vehicles_df, vehicle_velocities_df,
                  vehicle_capacities_df, road_capacities_df, asc_df):

    network_gdf = network_gdf.set_index("link_id")

    vehicles_list = vehicles_df.to_dict("records")
    vehicle_map = {r["vehicle"]: r for r in vehicles_list}

    velocities = {
        (r["vehicle"], r["road_type"]): r["velocity"]
        for _, r in vehicle_velocities_df.iterrows()
    }

    road_cap_map = {r["road_type"]: r["capacity"] for _, r in road_capacities_df.iterrows()}

    cap_map = {
        (r["vehicle"], r["resource"]): r["capacity"]
        for _, r in vehicle_capacities_df.iterrows()
    }

    asc_map = {
        (r["vehicle"], r["resource"]): r["alpha"]
        for _, r in asc_df.iterrows()
    }

    dwell_map = {r["resource"]: (r["dwell_time"], r["load_pct"]) for _, r in dwell_times_df.iterrows()}

    intervals = time_intervals_df["time_interval"].tolist()
    durations = {r["time_interval"]: r["duration"] for _, r in time_intervals_df.iterrows()}

    dep_map = {}
    for _, r in departures_df.iterrows():
        dep_map.setdefault(r["resource"], {})[r["time_interval"]] = r["probability"]

    resource_cols_supply = [c for c in desire_lines_gdf.columns
                            if c.endswith("_supply") and pd.api.types.is_numeric_dtype(desire_lines_gdf[c])]
    resource_cols_demand = [c for c in desire_lines_gdf.columns
                            if c.endswith("_demand") and pd.api.types.is_numeric_dtype(desire_lines_gdf[c])]
    resources = [c[:-len("_supply")] for c in resource_cols_supply]

    dl_flows = {}
    for dl_idx, dl_row in desire_lines_gdf.iterrows():
        geom = dl_row.geometry
        origin = geom.coords[0]
        dest = geom.coords[-1]
        for resource in resources:
            sup = dl_row.get(f"{resource}_supply", 0) or 0
            dem = dl_row.get(f"{resource}_demand", 0) or 0
            flow = min(sup, dem)
            if flow > 0:
                dl_flows[(dl_idx, resource)] = {"flow": flow, "origin": origin, "dest": dest}

    link_pcu_loads = {}
    output_rows = []

    in_flight = []

    cumulative_time = 0.0

    for interval in intervals:
        duration = durations[interval]

        node_coords, coord_index, edges, vehicle_graphs, link_lengths = _build_graph(
            network_gdf, vehicles_list, velocities, road_cap_map, link_pcu_loads, duration
        )

        if not node_coords:
            cumulative_time += duration
            continue

        kd_tree = KDTree(node_coords)

        edges_by_node_pair = {}
        for link_id, a, b, length, road_type, grade, direction, v_over_c in edges:
            if direction in ("both", "forward"):
                edges_by_node_pair[(a, b)] = link_id
            if direction in ("both", "backward"):
                edges_by_node_pair[(b, a)] = link_id

        dist_cache = {}
        pred_cache = {}

        interval_trips = []

        for resource in resources:
            if resource not in dep_map:
                continue
            prob = dep_map[resource].get(interval, 0.0)
            if prob <= 0:
                continue

            resource_dl = {k: dict(v) for k, v in dl_flows.items() if k[1] == resource}
            if not resource_dl:
                continue

            total_flow = sum(v["flow"] for v in resource_dl.values()) * prob
            remaining_flow = {k: v["flow"] * prob for k, v in resource_dl.items()}
            total_remaining = total_flow

            while total_remaining > 1e-9:
                weights = [(k, remaining_flow[k]) for k in remaining_flow if remaining_flow[k] > 1e-9]
                if not weights:
                    break
                keys = [w[0] for w in weights]
                probs = [w[1] for w in weights]
                total_w = sum(probs)
                probs_norm = [p / total_w for p in probs]
                u = random.random()
                cumsum = 0.0
                chosen_key = keys[-1]
                for k, p_k in zip(keys, probs_norm):
                    cumsum += p_k
                    if u <= cumsum:
                        chosen_key = k
                        break

                dl_idx, _ = chosen_key
                info = resource_dl[chosen_key]
                origin = info["origin"]
                dest = info["dest"]

                o_node = _snap(origin, kd_tree, node_coords)
                d_node = _snap(dest, kd_tree, node_coords)

                if o_node == d_node:
                    remaining_flow[chosen_key] = 0.0
                    total_remaining -= info["flow"] * prob
                    continue

                best_vehicle = None
                best_util = None
                best_route = None
                best_route_time = None
                best_route_dist = None

                for v_row in vehicles_list:
                    vehicle = v_row["vehicle"]
                    cap = cap_map.get((vehicle, resource), None)
                    if cap is None:
                        continue
                    asc = asc_map.get((vehicle, resource), 0.0)
                    time_cost = v_row["time_cost"]
                    dist_cost = v_row["distance_cost"]

                    cache_key = (vehicle, o_node)
                    if cache_key not in dist_cache:
                        g_csr, _ = vehicle_graphs[vehicle]
                        d, p = dijkstra(g_csr, directed=True, indices=o_node,
                                        return_predecessors=True)
                        dist_cache[cache_key] = d
                        pred_cache[cache_key] = p

                    route_time = dist_cache[cache_key][d_node]
                    if route_time == float("inf") or route_time <= 0:
                        continue

                    route = _route_links(pred_cache[cache_key], d_node, o_node, edges_by_node_pair)
                    if route is None:
                        continue

                    route_dist = sum(link_lengths.get(l, 0.0) for l in route)
                    util = asc + time_cost * route_time + dist_cost * route_dist

                    if best_util is None or util > best_util:
                        best_util = util
                        best_vehicle = vehicle
                        best_route = route
                        best_route_time = route_time
                        best_route_dist = route_dist

                if best_vehicle is None:
                    remaining_flow[chosen_key] = 0.0
                    total_remaining = sum(v for v in remaining_flow.values() if v > 1e-9)
                    continue

                cap = cap_map[(best_vehicle, resource)]
                units = min(remaining_flow[chosen_key], cap)
                load_pct = units / cap
                n_vehicles = 1
                pcu = vehicle_map[best_vehicle]["pcu"]

                interval_trips.append({
                    "vehicle": best_vehicle,
                    "route": best_route,
                    "n_vehicles": n_vehicles,
                    "pcu": pcu,
                    "load_pct": load_pct,
                    "resource": resource,
                    "origin": origin,
                    "dest": dest,
                    "o_node": o_node,
                    "d_node": d_node,
                    "departure_time": cumulative_time,
                })

                remaining_flow[chosen_key] -= units
                total_remaining -= units

        all_trips = interval_trips + in_flight
        next_in_flight = []

        link_contributions = {}

        for trip in all_trips:
            vehicle = trip["vehicle"]
            route = trip["route"]
            n_vehicles = trip["n_vehicles"]
            pcu = trip["pcu"]
            load_pct = trip["load_pct"]
            departure_time = trip["departure_time"]

            v_row = vehicle_map[vehicle]
            alpha = v_row["bpr_alpha"]
            beta = v_row["bpr_beta"]

            interval_start = cumulative_time
            interval_end = cumulative_time + duration

            current_time = departure_time
            remaining_route = list(route)

            for link_id in remaining_route:
                road_type = network_gdf.loc[link_id, "road_type"]
                grade = network_gdf.loc[link_id, "grade"]
                length = link_lengths.get(link_id, 0.0)
                cap = road_cap_map.get(road_type, 1.0)
                pcu_load = link_pcu_loads.get(link_id, 0.0)
                vel = velocities.get((vehicle, road_type), 1.0)
                eff_vel = vel * math.exp(-grade / 100.0)
                if eff_vel <= 0:
                    eff_vel = 1e-9
                t0 = length / eff_vel
                bpr = t0 * (1.0 + alpha * ((pcu_load / cap) ** beta if cap > 0 else 0.0))

                link_enter = current_time
                link_exit = current_time + bpr

                overlap_start = max(link_enter, interval_start)
                overlap_end = min(link_exit, interval_end)
                overlap = max(0.0, overlap_end - overlap_start)

                if overlap > 0 and bpr > 0:
                    fraction = overlap / bpr
                    key = (link_id, interval)
                    if key not in link_contributions:
                        link_contributions[key] = {}
                    vk = vehicle
                    if vk not in link_contributions[key]:
                        link_contributions[key][vk] = {"weighted_count": 0.0, "weighted_load": 0.0,
                                                        "weighted_vel": 0.0, "total_weight": 0.0}
                    contrib = n_vehicles * fraction
                    link_contributions[key][vk]["weighted_count"] += contrib
                    link_contributions[key][vk]["weighted_load"] += contrib * load_pct
                    link_contributions[key][vk]["weighted_vel"] += contrib * (length / bpr)
                    link_contributions[key][vk]["total_weight"] += contrib

                if link_exit > interval_end:
                    fraction_done = (interval_end - link_enter) / bpr if bpr > 0 else 0.0
                    next_in_flight.append({
                        **trip,
                        "route": [link_id] + [l for l in remaining_route if l != link_id],
                        "departure_time": interval_end - (bpr * (1.0 - fraction_done)),
                    })
                    break

                current_time = link_exit

            if current_time >= interval_end:
                continue

            dwell_time, ret_load_pct = dwell_map.get(trip["resource"], (0.0, 0.0))
            arrival_time = current_time
            current_idx = intervals.index(interval)
            fut_cumulative = cumulative_time
            return_departure_time = None
            for i, fut_interval in enumerate(intervals[current_idx:]):
                fut_cumulative += durations[fut_interval]
                if fut_cumulative >= arrival_time + dwell_time:
                    next_idx = current_idx + i + 1
                    if next_idx < len(intervals):
                        return_departure_time = fut_cumulative
                    break

            if return_departure_time is not None:
                o_node = trip["d_node"]
                d_node = trip["o_node"]
                if o_node != d_node:
                    ret_vehicle = trip["vehicle"]
                    ret_cache_key = (ret_vehicle, o_node)
                    if ret_cache_key not in dist_cache:
                        g_csr, _ = vehicle_graphs[ret_vehicle]
                        d, p = dijkstra(g_csr, directed=True, indices=o_node,
                                        return_predecessors=True)
                        dist_cache[ret_cache_key] = d
                        pred_cache[ret_cache_key] = p
                    ret_route_links = _route_links(
                        pred_cache[ret_cache_key], d_node, o_node, edges_by_node_pair
                    )
                    if ret_route_links:
                        next_in_flight.append({
                            "vehicle": ret_vehicle,
                            "route": ret_route_links,
                            "n_vehicles": math.ceil(n_vehicles * ret_load_pct),
                            "pcu": pcu,
                            "load_pct": ret_load_pct,
                            "resource": trip["resource"],
                            "origin": trip["dest"],
                            "dest": trip["origin"],
                            "o_node": o_node,
                            "d_node": d_node,
                            "departure_time": return_departure_time,
                        })

        for (link_id, intv), vehicle_data in link_contributions.items():
            for vehicle, data in vehicle_data.items():
                tw = data["total_weight"]
                if tw > 0:
                    link_pcu_loads[link_id] = link_pcu_loads.get(link_id, 0.0) + data["weighted_count"] * vehicle_map[vehicle]["pcu"]
                    output_rows.append({
                        "link_id": link_id,
                        "time_interval": intv,
                        "vehicle": vehicle,
                        "count": data["weighted_count"],
                        "velocity": data["weighted_vel"] / tw,
                        "load_pct": data["weighted_load"] / tw,
                    })

        in_flight = next_in_flight
        cumulative_time += duration

    return output_rows
