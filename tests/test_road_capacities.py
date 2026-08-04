from urban_dollop.synth.road_capacities import road_capacities


def test_zero_sigma_is_a_single_road_type():
    rows = road_capacities(sigma=0.0)
    assert len(rows) == 1
    assert rows[0]["road_type"] == "road_type_1"


def test_road_types_are_sequential_and_unique():
    rows = road_capacities(sigma=2.0)
    road_types = [r["road_type"] for r in rows]
    assert road_types == [f"road_type_{i + 1}" for i in range(len(rows))]


def test_capacities_are_positive():
    rows = road_capacities(sigma=2.0)
    assert all(r["capacity"] > 0 for r in rows)


def test_given_road_types_used_as_is_and_ignore_sigma_for_count():
    rows = road_capacities(road_types=["highway", "residential"], sigma=5.0)
    assert [r["road_type"] for r in rows] == ["highway", "residential"]
