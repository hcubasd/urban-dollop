from urban_dollop.synth.road_capacities import road_capacities


def test_returns_list_of_dicts():
    rows = road_capacities()
    assert isinstance(rows, list)
    assert all(isinstance(r, dict) for r in rows)


def test_has_required_columns():
    for row in road_capacities():
        assert "road_type" in row
        assert "capacity" in row


def test_capacity_is_positive():
    for row in road_capacities():
        assert row["capacity"] > 0.0


def test_road_type_names_sequential():
    rows = road_capacities()
    for i, row in enumerate(rows):
        assert row["road_type"] == f"road_type_{i + 1}"


def test_no_duplicate_road_types():
    rows = road_capacities()
    road_types = [r["road_type"] for r in rows]
    assert len(road_types) == len(set(road_types))
