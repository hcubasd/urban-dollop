from urban_dollop.synth.vehicle_velocities import vehicle_velocities


def test_zero_sigma_is_a_single_vehicle_single_road_type():
    rows = vehicle_velocities(sigma=0.0)
    assert len(rows) == 1
    assert rows[0]["vehicle"] == "vehicle_1"
    assert rows[0]["road_type"] == "road_type_1"


def test_full_cross_product():
    rows = vehicle_velocities(sigma=2.0)
    vehicles = {r["vehicle"] for r in rows}
    road_types = {r["road_type"] for r in rows}
    assert len(rows) == len(vehicles) * len(road_types)
    seen = {(r["vehicle"], r["road_type"]) for r in rows}
    assert seen == {(v, r) for v in vehicles for r in road_types}


def test_velocities_are_positive():
    rows = vehicle_velocities(sigma=2.0)
    assert all(r["velocity"] > 0 for r in rows)


def test_given_pairs_used_as_is_and_ignore_sigma_for_shape():
    pairs = [
        {"vehicle": "truck", "road_type": "highway"},
        {"vehicle": "bike", "road_type": "residential"},
    ]
    rows = vehicle_velocities(pairs=pairs, sigma=5.0)
    assert {(r["vehicle"], r["road_type"]) for r in rows} == {("truck", "highway"), ("bike", "residential")}
    assert all(r["velocity"] > 0 for r in rows)


def test_given_pairs_need_not_be_a_full_cross_product():
    pairs = [{"vehicle": "boat", "road_type": "waterway"}]
    rows = vehicle_velocities(pairs=pairs, sigma=1.0)
    assert len(rows) == 1
