from urban_dollop.synth.alternative_specific_constants import alternative_specific_constants


def test_returns_list_of_dicts():
    rows = alternative_specific_constants()
    assert isinstance(rows, list)
    assert all(isinstance(r, dict) for r in rows)


def test_has_required_columns():
    for row in alternative_specific_constants():
        assert "resource" in row
        assert "vehicle" in row
        assert "alpha" in row


def test_alpha_is_float():
    for row in alternative_specific_constants():
        assert isinstance(row["alpha"], float)


def test_full_cross_product():
    rows = alternative_specific_constants()
    pairs = [(r["resource"], r["vehicle"]) for r in rows]
    assert len(pairs) == len(set(pairs))
    resources = sorted(set(r["resource"] for r in rows))
    vehicles = sorted(set(r["vehicle"] for r in rows))
    assert len(rows) == len(resources) * len(vehicles)


def test_resource_names_sequential():
    rows = alternative_specific_constants()
    resources = list(dict.fromkeys(r["resource"] for r in rows))
    for i, name in enumerate(resources):
        assert name == f"resource_{i + 1}"


def test_vehicle_names_sequential():
    rows = alternative_specific_constants()
    vehicles = list(dict.fromkeys(r["vehicle"] for r in rows))
    for i, name in enumerate(vehicles):
        assert name == f"vehicle_{i + 1}"
