import bisect

import pandas as pd

from urban_dollop.synth.copert_v_coefficients import GRADIENT_BINS, PAYLOAD_BINS


def _snap(value, bins):
    idx = bisect.bisect_left(bins, value)
    if idx == 0:
        return bins[0]
    if idx == len(bins):
        return bins[-1]
    before, after = bins[idx - 1], bins[idx]
    return before if abs(value - before) <= abs(value - after) else after


def _copert_ef(row, velocity):
    alpha = row["alpha"]
    beta = row["beta"]
    gamma = row["gamma"]
    delta = row["delta"]
    epsilon = row["epsilon"]
    zeta = row["zeta"]
    eta = row["eta"]
    rf = row["rf"]
    if velocity <= 0:
        return 0.0
    numerator = alpha * velocity ** 2 + beta * velocity + gamma + delta / velocity
    denominator = epsilon * velocity ** 2 + zeta * velocity + eta
    if denominator == 0:
        return 0.0
    return max(0.0, numerator / denominator * (1.0 - rf))


def network_emissions(network_loads_df, network_gdf, vehicles_df,
                      copert_v_df, emission_factors_df):
    network_gdf = network_gdf.set_index("link_id")
    vehicle_type_map = {r["vehicle"]: r["vehicle_type"] for _, r in vehicles_df.iterrows()}

    copert_map = {}
    for _, r in copert_v_df.iterrows():
        copert_map.setdefault((r["vehicle_type"], r["pollutant"]), {})[
            (r["gradient_bin"], r["payload_bin"])
        ] = r

    ef_map = {}
    for _, r in emission_factors_df.iterrows():
        ef_map[(r["vehicle_type"], r["pollutant"])] = r["ef"]

    gradient_bins = sorted(GRADIENT_BINS)
    payload_bins = sorted(PAYLOAD_BINS)

    rows = []
    for _, load_row in network_loads_df.iterrows():
        link_id = load_row["link_id"]
        time_interval = load_row["time_interval"]
        vehicle = load_row["vehicle"]
        count = load_row["count"]
        velocity = load_row["velocity"]
        load_pct = load_row["load_pct"]

        if link_id not in network_gdf.index:
            continue
        link_row = network_gdf.loc[link_id]
        length = link_row.geometry.length
        grade = link_row["grade"]

        vehicle_type = vehicle_type_map.get(vehicle)
        if vehicle_type is None:
            continue

        gradient_bin = _snap(grade, gradient_bins)
        payload_bin = _snap(load_pct * 100.0, payload_bins)

        pollutants_done = set()

        for (vt, pollutant), bin_map in copert_map.items():
            if vt != vehicle_type:
                continue
            coeff_row = bin_map.get((gradient_bin, payload_bin))
            if coeff_row is None:
                continue
            ef = _copert_ef(coeff_row, velocity)
            grams = ef * length * count
            rows.append({
                "link_id": link_id,
                "time_interval": time_interval,
                "vehicle": vehicle,
                "pollutant": pollutant,
                "grams": grams,
            })
            pollutants_done.add(pollutant)

        for (vt, pollutant), ef in ef_map.items():
            if vt != vehicle_type or pollutant in pollutants_done:
                continue
            grams = ef * length * count
            rows.append({
                "link_id": link_id,
                "time_interval": time_interval,
                "vehicle": vehicle,
                "pollutant": pollutant,
                "grams": grams,
            })

    return rows
