import random

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point


def _sample_point(polygon):
    minx, miny, maxx, maxy = polygon.bounds
    while True:
        x = random.uniform(minx, maxx)
        y = random.uniform(miny, maxy)
        p = Point(x, y)
        if polygon.contains(p):
            return p


def _draw_batch(pairs):
    total = sum(p for _, p in pairs)
    u = random.random()
    cumulative = 0.0
    for size, prob in pairs:
        cumulative += prob / total
        if u <= cumulative:
            return size
    return pairs[-1][0]


def agents(supply_df, demand_df, batch_sizes_df, zones_gdf):
    zone_col = [c for c in zones_gdf.columns if c != "geometry" and pd.api.types.is_string_dtype(zones_gdf[c])][0]

    supply_strata = [c for c in supply_df.columns if pd.api.types.is_string_dtype(supply_df[c])]
    demand_strata = [c for c in demand_df.columns if pd.api.types.is_string_dtype(demand_df[c])]
    supply_resources = [c for c in supply_df.columns if pd.api.types.is_integer_dtype(supply_df[c])]
    demand_resources = [c for c in demand_df.columns if pd.api.types.is_integer_dtype(demand_df[c])]

    all_strata = list(dict.fromkeys(supply_strata + [c for c in demand_strata if c not in supply_strata]))

    batch_dist = {}
    for resource, group in batch_sizes_df.groupby("resource"):
        batch_dist[resource] = sorted(zip(group["batch_size"].tolist(), group["probability"].tolist()))

    all_resources = [
        r for r in dict.fromkeys(supply_resources + [c for c in demand_resources if c not in supply_resources])
        if r in batch_dist
    ]

    zone_lookup = dict(zip(zones_gdf[zone_col].tolist(), zones_gdf.geometry.tolist()))

    supply_work = supply_df.rename(columns={r: f"{r}_supply" for r in supply_resources})
    demand_work = demand_df.rename(columns={r: f"{r}_demand" for r in demand_resources})
    merge_on = [c for c in supply_strata if c in demand_strata]
    merged = supply_work.merge(demand_work, on=merge_on, how="outer")

    for r in all_resources:
        for suffix in ("_supply", "_demand"):
            col = f"{r}{suffix}"
            if col in merged.columns:
                merged[col] = merged[col].fillna(0).astype(int)
            else:
                merged[col] = 0

    rows = []
    for _, row in merged.iterrows():
        zone_value = row[zone_col]
        if pd.isna(zone_value) or zone_value not in zone_lookup:
            continue
        polygon = zone_lookup[zone_value]

        stratum_vals = {
            col: (row[col] if col in merged.columns and not pd.isna(row[col]) else None)
            for col in all_strata
        }

        remaining = {r: [int(row[f"{r}_supply"]), int(row[f"{r}_demand"])] for r in all_resources}

        while any(remaining[r][0] > 0 or remaining[r][1] > 0 for r in all_resources):
            agent = dict(stratum_vals)
            agent["geometry"] = _sample_point(polygon)
            for r in all_resources:
                batch = _draw_batch(batch_dist[r])
                s_take = min(batch, remaining[r][0])
                d_take = min(batch, remaining[r][1])
                agent[f"{r}_supply"] = s_take
                agent[f"{r}_demand"] = d_take
                remaining[r][0] -= s_take
                remaining[r][1] -= d_take
            rows.append(agent)

    if not rows:
        cols = all_strata + [f"{r}_supply" for r in all_resources] + [f"{r}_demand" for r in all_resources] + ["geometry"]
        return gpd.GeoDataFrame(columns=cols, crs=None)

    return gpd.GeoDataFrame(rows, crs=None)
