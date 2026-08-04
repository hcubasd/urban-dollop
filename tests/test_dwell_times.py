from urban_dollop.synth.dwell_times import dwell_times


def test_zero_sigma_is_a_single_resource():
    rows = dwell_times(sigma=0.0)
    assert len(rows) == 1
    assert rows[0]["resource"] == "resource_1"


def test_dwell_times_are_positive():
    rows = dwell_times(sigma=2.0)
    assert all(r["dwell_time"] > 0 for r in rows)


def test_load_pct_is_a_fraction():
    rows = dwell_times(sigma=2.0)
    assert all(0.0 <= r["load_pct"] < 1.0 for r in rows)


def test_resources_are_sequential_and_unique():
    rows = dwell_times(sigma=2.0)
    resources = [r["resource"] for r in rows]
    assert resources == [f"resource_{i + 1}" for i in range(len(rows))]


def test_given_resources_used_as_is_and_ignore_sigma_for_count():
    rows = dwell_times(resources=["grains", "parcels"], sigma=5.0)
    assert [r["resource"] for r in rows] == ["grains", "parcels"]
