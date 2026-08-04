from shapely.geometry import LineString

from urban_dollop.helpers.logistic import logistic
from urban_dollop.helpers.weighted_choice import weighted_choice


def _resource_names(agent_rows):
    if not agent_rows:
        return []
    cols = agent_rows[0].keys()
    capacities = {c[: -len("_capacity")] for c in cols if c.endswith("_capacity")}
    needs = {c[: -len("_need")] for c in cols if c.endswith("_need")}
    return sorted(capacities & needs)


def desire_lines(agent_rows):
    """One row per resource transaction between two agents: resource,
    quantity, and a 2-point geometry from provider to consumer. No agent
    identifiers -- nothing downstream needs to trace a line back to the
    agents that produced it, so they're not carried into the output.

    For each resource independently, agents.gpkg already carries
    everything needed (capacity, need, location) -- no batch_sizes.csv,
    no separate distribution to draw from. Repeatedly: the *currently*
    more-constrained side (whichever has less total remaining -- capacity
    or need -- rechecked every iteration, since depleting one pair changes
    both totals) picks a primary agent weighted by their own remaining
    value; the other side picks a secondary agent weighted by their
    remaining value times a distance decay from the primary agent (a
    gravity-model pairing -- closer agents are more likely matched,
    self-pairing excluded by agent_id). The transacted quantity is
    whichever of the two specific agents' remaining values is smaller --
    that's the "batch size" now, derived from the actual pair instead of
    sampled independently, and it's why batch_sizes.csv is gone. Both
    agents' remaining values are depleted by that quantity, and the loop
    continues until either total (recomputed fresh each pass) hits zero.

    Termination is guaranteed by construction, not a secondary check:
    weight *is* the remaining value, so a zero-remaining agent has zero
    weight and can never be drawn, so every drawn pair has strictly
    positive remaining on both sides and every iteration depletes a real,
    positive amount.
    """
    resources = _resource_names(agent_rows)
    if not agent_rows or not resources:
        return []

    remaining = {
        row["agent_id"]: {
            resource: {"capacity": row[f"{resource}_capacity"], "need": row[f"{resource}_need"]}
            for resource in resources
        }
        for row in agent_rows
    }
    points = {row["agent_id"]: row["geometry"] for row in agent_rows}

    rows = []
    for resource in resources:
        while True:
            capacity_side = [(aid, r[resource]["capacity"]) for aid, r in remaining.items() if r[resource]["capacity"] > 0]
            need_side = [(aid, r[resource]["need"]) for aid, r in remaining.items() if r[resource]["need"] > 0]
            total_capacity = sum(w for _, w in capacity_side)
            total_need = sum(w for _, w in need_side)
            if total_capacity == 0 or total_need == 0:
                break

            limiting = capacity_side if total_capacity <= total_need else need_side
            primary_id = weighted_choice([aid for aid, _ in limiting], [w for _, w in limiting])

            other_side = need_side if limiting is capacity_side else capacity_side
            candidates = [(aid, w) for aid, w in other_side if aid != primary_id]
            weights = [w * logistic(-points[primary_id].distance(points[aid])) for aid, w in candidates]
            if sum(weights) == 0:
                break
            secondary_id = weighted_choice([aid for aid, _ in candidates], weights)

            if limiting is capacity_side:
                provider_id, consumer_id = primary_id, secondary_id
            else:
                provider_id, consumer_id = secondary_id, primary_id

            quantity = min(remaining[provider_id][resource]["capacity"], remaining[consumer_id][resource]["need"])
            remaining[provider_id][resource]["capacity"] -= quantity
            remaining[consumer_id][resource]["need"] -= quantity

            rows.append({
                "resource": resource,
                "quantity": quantity,
                "geometry": LineString([points[provider_id].coords[0], points[consumer_id].coords[0]]),
            })
    return rows
