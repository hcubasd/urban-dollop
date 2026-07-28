from urban_dollop.synth.vehicle_capacities import vehicle_capacities


def test_returns_list_of_dicts():
    rows = vehicle_capacities()
    assert isinstance(rows, list)
    assert all(isinstance(r, dict) for r in rows)


def test_has_required_columns():
    for row in vehicle_capacities():
        assert "vehicle" in row
        assert "resource" in row
        assert "capacity" in row


def test_capacity_is_positive_integer():
    for row in vehicle_capacities():
        assert isinstance(row["capacity"], int)
        assert row["capacity"] >= 1


def test_full_cross_product():
    rows = vehicle_capacities()
    pairs = [(r["vehicle"], r["resource"]) for r in rows]
    assert len(pairs) == len(set(pairs))
    vehicles = sorted(set(r["vehicle"] for r in rows))
    resources = sorted(set(r["resource"] for r in rows))
    assert len(rows) == len(vehicles) * len(resources)


def test_vehicle_names_sequential():
    rows = vehicle_capacities()
    vehicles = list(dict.fromkeys(r["vehicle"] for r in rows))
    for i, name in enumerate(vehicles):
        assert name == f"vehicle_{i + 1}"


def test_resource_names_sequential():
    rows = vehicle_capacities()
    resources = list(dict.fromkeys(r["resource"] for r in rows))
    for i, name in enumerate(resources):
        assert name == f"resource_{i + 1}"
