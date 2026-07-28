from urban_dollop.synth.vehicle_velocities import vehicle_velocities


def test_returns_list_of_dicts():
    rows = vehicle_velocities()
    assert isinstance(rows, list)
    assert all(isinstance(r, dict) for r in rows)


def test_has_required_columns():
    for row in vehicle_velocities():
        assert "vehicle" in row
        assert "road_type" in row
        assert "velocity" in row


def test_velocity_is_positive():
    for row in vehicle_velocities():
        assert row["velocity"] > 0.0


def test_full_cross_product():
    rows = vehicle_velocities()
    pairs = [(r["vehicle"], r["road_type"]) for r in rows]
    assert len(pairs) == len(set(pairs))
    vehicles = sorted(set(r["vehicle"] for r in rows))
    road_types = sorted(set(r["road_type"] for r in rows))
    assert len(rows) == len(vehicles) * len(road_types)


def test_vehicle_names_sequential():
    rows = vehicle_velocities()
    vehicles = list(dict.fromkeys(r["vehicle"] for r in rows))
    for i, name in enumerate(vehicles):
        assert name == f"vehicle_{i + 1}"


def test_road_type_names_sequential():
    rows = vehicle_velocities()
    road_types = list(dict.fromkeys(r["road_type"] for r in rows))
    for i, name in enumerate(road_types):
        assert name == f"road_type_{i + 1}"
