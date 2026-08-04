from urban_dollop.synth.departures import departures


def test_zero_sigma_is_a_single_resource_single_interval():
    rows = departures(sigma=0.0)
    assert len(rows) == 1
    assert rows[0]["resource"] == "resource_1"
    assert rows[0]["time_interval"] == "interval_1"
    assert rows[0]["probability"] == 1.0


def test_each_resources_probabilities_sum_to_one():
    rows = departures(sigma=2.0)
    by_resource = {}
    for row in rows:
        by_resource.setdefault(row["resource"], []).append(row["probability"])
    for probs in by_resource.values():
        assert abs(sum(probs) - 1.0) < 1e-9


def test_probabilities_are_non_negative():
    rows = departures(sigma=2.0)
    assert all(row["probability"] >= 0.0 for row in rows)


def test_every_resource_uses_at_least_one_interval():
    rows = departures(sigma=2.0)
    by_resource = {}
    for row in rows:
        by_resource.setdefault(row["resource"], []).append(row["time_interval"])
    assert all(len(intervals) >= 1 for intervals in by_resource.values())


def test_a_resources_intervals_are_a_subset_of_the_shared_menu():
    rows = departures(sigma=3.0)
    all_intervals = {row["time_interval"] for row in rows}
    menu_size = max(int(i.split("_")[1]) for i in all_intervals)
    full_menu = {f"interval_{j + 1}" for j in range(menu_size)}
    assert all_intervals <= full_menu


def test_given_pairs_used_as_is_and_ignore_sigma_for_shape():
    pairs = [
        {"resource": "grains", "time_interval": "AM_peak"},
        {"resource": "grains", "time_interval": "PM_peak"},
        {"resource": "parcels", "time_interval": "midday"},
    ]
    rows = departures(pairs=pairs, sigma=5.0)
    assert {(r["resource"], r["time_interval"]) for r in rows} == {
        ("grains", "AM_peak"), ("grains", "PM_peak"), ("parcels", "midday"),
    }
    grains_probs = [r["probability"] for r in rows if r["resource"] == "grains"]
    assert abs(sum(grains_probs) - 1.0) < 1e-9
    parcels_probs = [r["probability"] for r in rows if r["resource"] == "parcels"]
    assert parcels_probs == [1.0]
