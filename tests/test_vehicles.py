from urban_dollop.synth.vehicles import vehicles


def test_zero_sigma_is_a_single_vehicle():
    rows = vehicles(sigma=0.0)
    assert len(rows) == 1
    assert rows[0]["vehicle"] == "vehicle_1"
    assert rows[0]["vehicle_type"] == "vehicle_type_1"


def test_vehicles_are_sequential_and_unique():
    rows = vehicles(sigma=2.0)
    vehicle_list = [r["vehicle"] for r in rows]
    assert vehicle_list == [f"vehicle_{i + 1}" for i in range(len(rows))]


def test_bpr_alpha_within_calibrated_bounds():
    rows = vehicles(sigma=2.0)
    assert all(0.05 <= r["bpr_alpha"] <= 2.0 for r in rows)


def test_bpr_beta_within_calibrated_bounds():
    rows = vehicles(sigma=2.0)
    assert all(2.0 <= r["bpr_beta"] <= 10.0 for r in rows)


def test_time_and_distance_coefficients_are_negative():
    rows = vehicles(sigma=2.0)
    assert all(r["time_coefficient"] < 0 for r in rows)
    assert all(r["distance_coefficient"] < 0 for r in rows)


def test_pcu_is_positive():
    rows = vehicles(sigma=2.0)
    assert all(r["pcu"] > 0 for r in rows)


def test_given_vehicle_list_used_as_is_and_ignore_sigma_for_count():
    rows = vehicles(vehicle_list=["truck", "van"], sigma=5.0)
    assert [r["vehicle"] for r in rows] == ["truck", "van"]
