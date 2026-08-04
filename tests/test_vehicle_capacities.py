from urban_dollop.synth.vehicle_capacities import vehicle_capacities


def test_zero_sigma_is_a_single_vehicle_single_resource():
    rows = vehicle_capacities(sigma=0.0)
    assert len(rows) == 1
    assert rows[0]["vehicle"] == "vehicle_1"
    assert rows[0]["resource"] == "resource_1"


def test_full_cross_product():
    rows = vehicle_capacities(sigma=2.0)
    vehicles = {r["vehicle"] for r in rows}
    resources = {r["resource"] for r in rows}
    assert len(rows) == len(vehicles) * len(resources)
    seen = {(r["vehicle"], r["resource"]) for r in rows}
    assert seen == {(v, r) for v in vehicles for r in resources}


def test_capacities_are_positive_whole_numbers():
    rows = vehicle_capacities(sigma=2.0)
    assert all(r["capacity"] > 0 and float(r["capacity"]).is_integer() for r in rows)


def test_given_pairs_used_as_is_and_ignore_sigma_for_shape():
    pairs = [
        {"vehicle": "truck", "resource": "grains"},
        {"vehicle": "van", "resource": "parcels"},
    ]
    rows = vehicle_capacities(pairs=pairs, sigma=5.0)
    assert {(r["vehicle"], r["resource"]) for r in rows} == {("truck", "grains"), ("van", "parcels")}
    assert all(float(r["capacity"]).is_integer() for r in rows)


def test_given_pairs_need_not_be_a_full_cross_product():
    pairs = [{"vehicle": "boat", "resource": "containers"}]
    rows = vehicle_capacities(pairs=pairs, sigma=1.0)
    assert len(rows) == 1
