from urban_dollop.synth.consolidation_radii import consolidation_radii


def test_zero_sigma_is_a_single_vehicle_single_resource():
    rows = consolidation_radii(sigma=0.0)
    assert len(rows) == 1
    assert rows[0]["vehicle"] == "vehicle_1"
    assert rows[0]["resource"] == "resource_1"


def test_full_cross_product_has_positive_radii():
    rows = consolidation_radii(sigma=2.0)
    vehicles = {row["vehicle"] for row in rows}
    resources = {row["resource"] for row in rows}
    assert len(rows) == len(vehicles) * len(resources)
    assert all(row["radius"] > 0 for row in rows)


def test_given_pairs_define_the_shape():
    pairs = [{"vehicle": "truck", "resource": "grains"}]
    assert consolidation_radii(pairs, sigma=5.0)[0]["vehicle"] == "truck"
    assert consolidation_radii(pairs, sigma=5.0)[0]["resource"] == "grains"
