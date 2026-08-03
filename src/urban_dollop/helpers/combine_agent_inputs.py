def _is_empty(value):
    return value is None or (isinstance(value, float) and value != value)  # NaN != NaN


def _normalize(value):
    # supply.csv/demand.csv/capacities.csv/needs.csv/zones.gpkg are four+one
    # independently-synthesized files -- a numeric zone_id can silently
    # stringify on a CSV round-trip if its file also has string-labeled
    # sibling dimensions (see the effects.csv dtype notes), while a
    # zones.gpkg-only zone_id never does (no sibling dimensions to trigger
    # it there). Comparing raw values across files risks a silent
    # int-vs-string mismatch; comparing string(value) everywhere avoids it.
    return str(value)


def _stratum_dims(rows, exclude):
    if not rows:
        return set()
    return set(rows[0]) - exclude


def _stratum_key(row, dims):
    return tuple(sorted((dim, _normalize(row[dim])) for dim in dims))


def combine_agent_inputs(supply_rows, demand_rows, capacities_rows, needs_rows, zones_gdf):
    """Match supply.csv, demand.csv, capacities.csv, needs.csv, and
    zones.gpkg -- four independently-synthesized files plus a fifth
    independent geometry source -- into per-stratum contexts ready for
    agent synthesis.

    A stratum combination is only usable if it's resolvable identically
    across every source: the stratum *dimension set* must match exactly
    (not just overlap) between all four data files, since a dimension
    present in one file but not another means their notion of "stratum"
    isn't even the same shape -- there'd be no principled way to pick
    which of that dimension's values an agent should carry. Given that,
    a resource is only usable for a specific stratum combination if it
    has a defined value in *all four* files for that combination: supply
    and demand each need a real aggregate (not an omitted cell), and
    capacities and needs each need an actual PMF (at least one row).
    Missing any one of the four means no agent can be given a valid,
    well-defined value for that resource in that stratum -- see
    synth/agents.py for why that has to halt agent generation entirely
    rather than skip just that resource.

    Returns a list of dicts, one per usable stratum combination:
    "dims" (the stratum's dimension values, for writing to output),
    "polygon" (that zone's geometry), and "resources" (a dict of
    resource -> {"supply", "demand", "capacity_pmf", "need_pmf"}).
    """
    capacity_resources = {row["resource"] for row in capacities_rows}
    need_resources = {row["resource"] for row in needs_rows}
    candidate_resources = capacity_resources | need_resources

    supply_dims = _stratum_dims(supply_rows, candidate_resources)
    demand_dims = _stratum_dims(demand_rows, candidate_resources)
    capacities_dims = _stratum_dims(capacities_rows, {"resource", "resource_level", "probability"})
    needs_dims = _stratum_dims(needs_rows, {"resource", "resource_level", "probability"})

    if not supply_dims or not (supply_dims == demand_dims == capacities_dims == needs_dims):
        return []
    dims = supply_dims
    if "zone_id" not in dims:
        return []

    zone_lookup = {}
    zone_id_display = {}
    for _, zrow in zones_gdf.iterrows():
        if zrow.geometry is None:
            continue
        normalized = _normalize(zrow["zone_id"])
        zone_lookup[normalized] = zrow.geometry
        zone_id_display[normalized] = zrow["zone_id"]

    display = {}
    supply_lookup = {}
    for row in supply_rows:
        key = _stratum_key(row, dims)
        display.setdefault(key, {dim: row[dim] for dim in dims})
        for resource in candidate_resources:
            if resource in row and not _is_empty(row[resource]):
                supply_lookup.setdefault(key, {})[resource] = row[resource]

    demand_lookup = {}
    for row in demand_rows:
        key = _stratum_key(row, dims)
        display.setdefault(key, {dim: row[dim] for dim in dims})
        for resource in candidate_resources:
            if resource in row and not _is_empty(row[resource]):
                demand_lookup.setdefault(key, {})[resource] = row[resource]

    capacities_pmf = {}
    for row in capacities_rows:
        key = _stratum_key(row, dims)
        display.setdefault(key, {dim: row[dim] for dim in dims})
        capacities_pmf.setdefault(key, {}).setdefault(row["resource"], []).append(
            (row["resource_level"], row["probability"])
        )

    needs_pmf = {}
    for row in needs_rows:
        key = _stratum_key(row, dims)
        display.setdefault(key, {dim: row[dim] for dim in dims})
        needs_pmf.setdefault(key, {}).setdefault(row["resource"], []).append(
            (row["resource_level"], row["probability"])
        )

    contexts = []
    common_keys = supply_lookup.keys() & demand_lookup.keys() & capacities_pmf.keys() & needs_pmf.keys()
    for key in common_keys:
        key_dict = dict(key)
        zone_norm = key_dict["zone_id"]
        if zone_norm not in zone_lookup:
            continue
        eligible_resources = (
            candidate_resources
            & supply_lookup[key].keys()
            & demand_lookup[key].keys()
            & capacities_pmf[key].keys()
            & needs_pmf[key].keys()
        )
        if not eligible_resources:
            continue
        row_dims = dict(display[key])
        row_dims["zone_id"] = zone_id_display[zone_norm]
        contexts.append({
            "dims": row_dims,
            "polygon": zone_lookup[zone_norm],
            "resources": {
                resource: {
                    "supply": supply_lookup[key][resource],
                    "demand": demand_lookup[key][resource],
                    "capacity_pmf": sorted(capacities_pmf[key][resource]),
                    "need_pmf": sorted(needs_pmf[key][resource]),
                }
                for resource in eligible_resources
            },
        })
    return contexts
