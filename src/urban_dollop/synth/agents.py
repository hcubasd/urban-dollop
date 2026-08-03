from urban_dollop.helpers.combine_agent_inputs import combine_agent_inputs
from urban_dollop.helpers.sample_point import sample_point
from urban_dollop.helpers.truncated_draw import truncated_draw


def agents(supply_rows, demand_rows, capacities_rows, needs_rows, zones_gdf):
    """One row per synthesized agent: agent_id, geometry, the stratum's
    dimension values, and {resource}_capacity/{resource}_need for every
    resource usable in that stratum (see combine_agent_inputs).

    Agents are drawn one at a time per stratum, depleting that stratum's
    supply/demand budget as they go. Each draw independently truncates
    the capacity distribution to the remaining supply and the need
    distribution to the remaining demand (renormalized), then draws one
    value from each via a uniform(0, 1) -- capacity and need for the same
    resource are independent draws, not shared. An agent is a single
    coherent record: if *any* resource can't produce a valid draw (no
    remaining-feasible level in its distribution), no valid agent can be
    produced at all, so generation for that stratum halts entirely --
    not just for that one resource -- since every subsequent attempt
    would face equal-or-worse depletion and fail the same way.

    A second halt condition catches a case infeasibility alone doesn't:
    every draw is technically feasible but reduces no remaining budget at
    all, e.g. a resource whose only synthesized level in a stratum is 0
    -- 0 is always <= any non-negative remaining budget, so this would
    never trip the infeasibility halt and would draw forever, all zeros,
    without ever making progress. If a round makes zero progress on
    every tracked resource's supply and demand simultaneously, that
    agent is still committed (it's a legitimate, valid draw), but
    generation then halts immediately afterward -- by the same
    idempotency argument as the truncation logic itself, every
    subsequent round would face the identical state and repeat forever.
    """
    contexts = combine_agent_inputs(supply_rows, demand_rows, capacities_rows, needs_rows, zones_gdf)

    rows = []
    agent_id = 0
    for context in contexts:
        remaining = {
            resource: {"supply": info["supply"], "demand": info["demand"]}
            for resource, info in context["resources"].items()
        }
        while True:
            draws = {}
            for resource, info in context["resources"].items():
                capacity = truncated_draw(info["capacity_pmf"], remaining[resource]["supply"])
                need = truncated_draw(info["need_pmf"], remaining[resource]["demand"])
                if capacity is None or need is None:
                    draws = None
                    break
                draws[resource] = (capacity, need)
            if draws is None:
                break

            agent_id += 1
            row = dict(context["dims"])
            row["agent_id"] = agent_id
            row["geometry"] = sample_point(context["polygon"])
            made_progress = False
            for resource, (capacity, need) in draws.items():
                row[f"{resource}_capacity"] = capacity
                row[f"{resource}_need"] = need
                remaining[resource]["supply"] -= capacity
                remaining[resource]["demand"] -= need
                made_progress = made_progress or capacity != 0 or need != 0
            rows.append(row)
            if not made_progress:
                break
    return rows
