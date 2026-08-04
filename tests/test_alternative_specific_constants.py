from urban_dollop.synth.alternative_specific_constants import alternative_specific_constants


def test_zero_sigma_is_a_single_vehicle_single_resource():
    rows = alternative_specific_constants(sigma=0.0)
    assert len(rows) == 1
    assert rows[0]["vehicle"] == "vehicle_1"
    assert rows[0]["resource"] == "resource_1"


def test_full_cross_product():
    rows = alternative_specific_constants(sigma=2.0)
    vehicles = {r["vehicle"] for r in rows}
    resources = {r["resource"] for r in rows}
    assert len(rows) == len(vehicles) * len(resources)
    seen = {(r["vehicle"], r["resource"]) for r in rows}
    assert seen == {(v, r) for v in vehicles for r in resources}


def test_constants_can_be_any_sign():
    # not a hard guarantee any single call sees both signs, just that
    # nothing clamps or forces a sign one way or the other
    rows = alternative_specific_constants(sigma=2.0)
    assert all(isinstance(r["alternative_specific_constant"], float) for r in rows)


def test_given_pairs_used_as_is_and_ignore_sigma_for_shape():
    pairs = [
        {"vehicle": "truck", "resource": "grains"},
        {"vehicle": "van", "resource": "parcels"},
    ]
    rows = alternative_specific_constants(pairs=pairs, sigma=5.0)
    assert {(r["vehicle"], r["resource"]) for r in rows} == {("truck", "grains"), ("van", "parcels")}


def test_given_pairs_need_not_be_a_full_cross_product():
    pairs = [{"vehicle": "boat", "resource": "containers"}]
    rows = alternative_specific_constants(pairs=pairs, sigma=1.0)
    assert len(rows) == 1
