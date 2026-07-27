import random

import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString

from urban_dollop.helpers.logistic import logistic


def _draw_batch(pairs):
    total = sum(p for _, p in pairs)
    u = random.random()
    cumulative = 0.0
    for size, prob in pairs:
        cumulative += prob / total
        if u <= cumulative:
            return size
    return pairs[-1][0]


def _weighted_choice(weights):
    total = sum(weights)
    u = random.random() * total
    cumulative = 0.0
    for i, w in enumerate(weights):
        cumulative += w
        if u <= cumulative:
            return i
    return len(weights) - 1


def desire_lines(agents_gdf, batch_sizes_df):
    supply_cols = [c for c in agents_gdf.columns if c.endswith("_supply") and pd.api.types.is_integer_dtype(agents_gdf[c])]
    resources = [c[:-len("_supply")] for c in supply_cols]
    resources = [r for r in resources if f"{r}_demand" in agents_gdf.columns]

    batch_dist = {}
    for resource, group in batch_sizes_df.groupby("resource"):
        batch_dist[resource] = sorted(zip(group["batch_size"].tolist(), group["probability"].tolist()))

    resources = [r for r in resources if r in batch_dist]

    all_supply_cols = [f"{r}_supply" for r in resources]
    all_demand_cols = [f"{r}_demand" for r in resources]

    rows = []
    for resource in resources:
        supply_col = f"{resource}_supply"
        demand_col = f"{resource}_demand"

        supply_agents = agents_gdf[agents_gdf[supply_col] > 0].reset_index(drop=True)
        demand_agents = agents_gdf[agents_gdf[demand_col] > 0].reset_index(drop=True)

        if supply_agents.empty or demand_agents.empty:
            continue

        total_supply = int(supply_agents[supply_col].sum())
        total_demand = int(demand_agents[demand_col].sum())
        remaining = min(total_supply, total_demand)

        supply_weights = supply_agents[supply_col].tolist()
        demand_weights_base = demand_agents[demand_col].tolist()
        supply_points = supply_agents.geometry.tolist()
        demand_points = demand_agents.geometry.tolist()

        while remaining > 0:
            s_idx = _weighted_choice(supply_weights)
            s_point = supply_points[s_idx]

            decay = [
                0.0 if d.equals(s_point) else w * logistic(-s_point.distance(d))
                for w, d in zip(demand_weights_base, demand_points)
            ]
            if sum(decay) == 0.0:
                break
            d_idx = _weighted_choice(decay)
            d_point = demand_points[d_idx]

            batch = min(_draw_batch(batch_dist[resource]), remaining)

            row = {c: 0 for c in all_supply_cols + all_demand_cols}
            row[supply_col] = batch
            row[demand_col] = batch
            row["geometry"] = LineString([s_point.coords[0], d_point.coords[0]])
            rows.append(row)

            remaining -= batch

    if not rows:
        cols = all_supply_cols + all_demand_cols + ["geometry"]
        return gpd.GeoDataFrame(columns=cols, crs=None)

    return gpd.GeoDataFrame(rows, crs=None)
