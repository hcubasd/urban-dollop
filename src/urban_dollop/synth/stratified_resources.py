from urban_dollop.helpers.logistic import logistic


def stratified_resources(slopes_rows, thresholds_rows):
    resources = {}
    for row in thresholds_rows:
        resources.setdefault(row["resource"], []).append(row)
    for levels in resources.values():
        levels.sort(key=lambda r: r["resource_level"])

    stratum_cols = [k for k in slopes_rows[0] if k != "slope"]

    output = []
    for slope_row in slopes_rows:
        beta = slope_row["slope"]
        out = {col: slope_row[col] for col in stratum_cols}
        for resource, levels in resources.items():
            thresholds = [r["threshold"] for r in levels if r["threshold"] is not None]
            level_values = [r["resource_level"] for r in levels]
            cum_probs = [0.0] + [logistic(mu - beta) for mu in thresholds] + [1.0]
            out[resource] = round(sum(
                level_values[k] * (cum_probs[k + 1] - cum_probs[k])
                for k in range(len(level_values))
            ))
        output.append(out)

    return output
