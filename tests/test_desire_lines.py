from shapely.geometry import Point

from urban_dollop.synth.desire_lines import desire_lines


def test_empty_agents():
    assert desire_lines([]) == []


def test_no_matching_capacity_need_column_pairs():
    agents = [{"agent_id": 1, "zone_id": 1, "geometry": Point(0, 0), "grains_capacity": 3}]
    assert desire_lines(agents) == []


def test_exhausts_the_smaller_total_and_stops():
    agents = [
        {"agent_id": 1, "zone_id": 1, "geometry": Point(0.1, 0.1), "grains_capacity": 8, "grains_need": 0},
        {"agent_id": 2, "zone_id": 2, "geometry": Point(0.9, 0.9), "grains_capacity": 0, "grains_need": 5},
    ]
    rows = desire_lines(agents)
    assert sum(r["quantity"] for r in rows) == 5
    assert all(r["resource"] == "grains" for r in rows)


def test_line_direction_is_provider_to_consumer():
    agents = [
        {"agent_id": 1, "zone_id": 1, "geometry": Point(0.1, 0.1), "grains_capacity": 5, "grains_need": 0},
        {"agent_id": 2, "zone_id": 2, "geometry": Point(0.9, 0.9), "grains_capacity": 0, "grains_need": 5},
    ]
    rows = desire_lines(agents)
    assert len(rows) == 1
    start, end = list(rows[0]["geometry"].coords)
    assert start == (0.1, 0.1)
    assert end == (0.9, 0.9)


def test_origin_agent_and_geometry_follow_the_line_direction():
    agents = [
        {"agent_id": 1, "zone_id": 10, "geometry": Point(0.1, 0.1), "grains_capacity": 5, "grains_need": 0},
        {"agent_id": 2, "zone_id": 20, "geometry": Point(0.9, 0.9), "grains_capacity": 0, "grains_need": 5},
    ]
    rows = desire_lines(agents)
    assert len(rows) == 1
    # provider is agent 1 and the endpoint is consumer agent 2
    assert rows[0]["origin_agent_id"] == 1
    assert list(rows[0]["geometry"].coords)[-1] == (0.9, 0.9)


def test_desire_lines_do_not_carry_destination_zone_ids():
    agents = [
        {"agent_id": 1, "zone_id": 10, "geometry": Point(0.1, 0.1), "grains_capacity": 10, "grains_need": 0},
        {"agent_id": 2, "zone_id": 20, "geometry": Point(0.8, 0.8), "grains_capacity": 0, "grains_need": 5},
        {"agent_id": 3, "zone_id": 20, "geometry": Point(0.9, 0.9), "grains_capacity": 0, "grains_need": 5},
    ]
    rows = desire_lines(agents)
    assert {r["origin_agent_id"] for r in rows} == {1}
    assert all("destination_zone_id" not in row for row in rows)


def test_single_agent_cannot_pair_with_itself():
    agents = [{"agent_id": 1, "zone_id": 1, "geometry": Point(0.1, 0.1), "grains_capacity": 5, "grains_need": 5}]
    assert desire_lines(agents) == []


def test_ragged_agents_with_nan_for_untracked_resources_are_excluded_not_crashed():
    nan = float("nan")
    agents = [
        {"agent_id": 1, "zone_id": 1, "geometry": Point(0.1, 0.1), "grains_capacity": 5, "grains_need": 0, "parcels_capacity": nan, "parcels_need": nan},
        {"agent_id": 2, "zone_id": 2, "geometry": Point(0.2, 0.2), "grains_capacity": 0, "grains_need": 5, "parcels_capacity": nan, "parcels_need": nan},
        {"agent_id": 3, "zone_id": 3, "geometry": Point(0.8, 0.8), "grains_capacity": nan, "grains_need": nan, "parcels_capacity": 3, "parcels_need": 0},
        {"agent_id": 4, "zone_id": 4, "geometry": Point(0.9, 0.9), "grains_capacity": nan, "grains_need": nan, "parcels_capacity": 0, "parcels_need": 3},
    ]
    rows = desire_lines(agents)
    resources_transacted = {r["resource"]: r["quantity"] for r in rows}
    assert resources_transacted == {"grains": 5, "parcels": 3}


def test_multiple_resources_between_same_pair_are_separate_rows():
    agents = [
        {"agent_id": 1, "zone_id": 1, "geometry": Point(0.1, 0.1), "grains_capacity": 3, "grains_need": 0, "parcels_capacity": 2, "parcels_need": 0},
        {"agent_id": 2, "zone_id": 2, "geometry": Point(0.9, 0.9), "grains_capacity": 0, "grains_need": 3, "parcels_capacity": 0, "parcels_need": 2},
    ]
    rows = desire_lines(agents)
    assert len(rows) == 2
    assert {r["resource"] for r in rows} == {"grains", "parcels"}


def test_never_produces_zero_quantity_rows():
    agents = [
        {"agent_id": i, "zone_id": i % 3, "geometry": Point(0.01 * i, 0.01 * i), "grains_capacity": (i % 3), "grains_need": ((i + 1) % 3)}
        for i in range(1, 15)
    ]
    rows = desire_lines(agents)
    assert all(r["quantity"] > 0 for r in rows)


def test_real_world_scale_coordinates_do_not_overflow():
    # A bare logistic(-distance) overflows math.exp once agents are much more
    # than ~700 units apart -- e.g. real projected coordinates (UTM metres),
    # not the unit square this pipeline synthesizes on. Distance is
    # normalized by the agent cloud's own extent specifically so this stays
    # well-behaved regardless of what units the geometry is in.
    agents = [
        {"agent_id": 1, "zone_id": 1, "geometry": Point(500_000, 4_649_776), "grains_capacity": 5, "grains_need": 0},
        {"agent_id": 2, "zone_id": 2, "geometry": Point(500_900, 4_650_500), "grains_capacity": 0, "grains_need": 5},
    ]
    rows = desire_lines(agents)
    assert sum(r["quantity"] for r in rows) == 5


def test_pairing_odds_are_scale_invariant():
    # One depot, three consumers at 1x/2x/3x spacing, only enough supply for
    # one -- so which one gets served reveals the decay's actual shape.
    # Repeated at unit-square scale and at a real-world-sized scale; a
    # correctly normalized decay gives (approximately) the same odds either
    # way, since it's the *relative* spacing that should matter, not the
    # absolute numbers.
    def build(scale):
        agents = [{"agent_id": 0, "zone_id": 0, "geometry": Point(0, 0), "grains_capacity": 1, "grains_need": 0}]
        for i, d in enumerate([1, 2, 3], start=1):
            agents.append({
                "agent_id": i, "zone_id": i, "geometry": Point(d * scale, 0),
                "grains_capacity": 0, "grains_need": 1,
            })
        return agents

    def nearest_share(scale, trials=1500):
        hits = sum(
            1
            for _ in range(trials)
            if list(desire_lines(build(scale))[0]["geometry"].coords)[-1] == (1 * scale, 0)
        )
        return hits / trials

    small = nearest_share(0.3)
    large = nearest_share(300_000)
    assert abs(small - large) < 0.1


def test_coincident_agents_do_not_divide_by_zero():
    # Every agent at the same point -- the bounding-box diagonal is 0, which
    # would divide-by-zero without a guard. Distance between them is also
    # always 0 regardless of the scale used, so pairing still has to work.
    agents = [
        {"agent_id": 1, "zone_id": 1, "geometry": Point(5, 5), "grains_capacity": 3, "grains_need": 0},
        {"agent_id": 2, "zone_id": 2, "geometry": Point(5, 5), "grains_capacity": 0, "grains_need": 3},
    ]
    rows = desire_lines(agents)
    assert sum(r["quantity"] for r in rows) == 3
