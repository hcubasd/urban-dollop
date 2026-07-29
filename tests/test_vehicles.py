from urban_dollop.synth.vehicles import vehicles


def test_returns_list_of_dicts():
    rows = vehicles()
    assert isinstance(rows, list)
    assert all(isinstance(r, dict) for r in rows)


def test_has_required_columns():
    for row in vehicles():
        assert "vehicle" in row
        assert "vehicle_type" in row
        assert "bpr_alpha" in row
        assert "bpr_beta" in row
        assert "time_cost" in row
        assert "distance_cost" in row
        assert "pcu" in row


def test_vehicle_names_sequential():
    rows = vehicles()
    for i, row in enumerate(rows):
        assert row["vehicle"] == f"vehicle_{i + 1}"


def test_bpr_alpha_is_positive():
    for row in vehicles():
        assert row["bpr_alpha"] > 0.0


def test_bpr_beta_is_positive():
    for row in vehicles():
        assert row["bpr_beta"] > 0.0


def test_vehicle_type_is_string():
    for row in vehicles():
        assert isinstance(row["vehicle_type"], str)
        assert row["vehicle_type"].startswith("vehicle_type_")


def test_pcu_is_positive():
    for row in vehicles():
        assert row["pcu"] > 0.0


def test_no_duplicate_vehicles():
    rows = vehicles()
    vehicle_names = [r["vehicle"] for r in rows]
    assert len(vehicle_names) == len(set(vehicle_names))
