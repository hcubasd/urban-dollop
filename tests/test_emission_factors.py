from urban_dollop.synth.emission_factors import emission_factors


def test_zero_sigma_is_a_single_vehicle_type_single_pollutant():
    rows = emission_factors(sigma=0.0)
    assert len(rows) == 1
    assert rows[0]["vehicle_type"] == "vehicle_type_1"
    assert rows[0]["pollutant"] == "pollutant_1"


def test_full_cross_product():
    rows = emission_factors(sigma=2.0)
    vehicle_types = {r["vehicle_type"] for r in rows}
    pollutants = {r["pollutant"] for r in rows}
    assert len(rows) == len(vehicle_types) * len(pollutants)
    seen = {(r["vehicle_type"], r["pollutant"]) for r in rows}
    assert seen == {(vt, p) for vt in vehicle_types for p in pollutants}


def test_emission_factor_is_positive():
    rows = emission_factors(sigma=2.0)
    assert all(r["emission_factor"] > 0 for r in rows)


def test_given_pairs_used_as_is_and_ignore_sigma_for_shape():
    pairs = [
        {"vehicle_type": "hdv", "pollutant": "pm10"},
        {"vehicle_type": "ldv", "pollutant": "pm25"},
    ]
    rows = emission_factors(pairs=pairs, sigma=5.0)
    assert {(r["vehicle_type"], r["pollutant"]) for r in rows} == {("hdv", "pm10"), ("ldv", "pm25")}


def test_given_pairs_need_not_be_a_full_cross_product():
    pairs = [{"vehicle_type": "hdv", "pollutant": "pm10"}]
    rows = emission_factors(pairs=pairs, sigma=1.0)
    assert len(rows) == 1
