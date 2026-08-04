from urban_dollop.helpers.weighted_choice import weighted_choice


def test_single_item_always_chosen():
    assert weighted_choice(["a"], [5]) == "a"


def test_zero_weight_never_chosen():
    for _ in range(200):
        assert weighted_choice(["a", "b"], [0, 1]) == "b"


def test_respects_relative_weights():
    counts = {"a": 0, "b": 0}
    for _ in range(2000):
        counts[weighted_choice(["a", "b"], [9, 1])] += 1
    # roughly 90/10 -- generous tolerance, this just needs to not be ~50/50
    assert counts["a"] > counts["b"] * 3
