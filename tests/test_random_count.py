from urban_dollop.helpers.random_count import random_count


def test_zero_sigma_is_deterministic_minimum():
    assert all(random_count(0.0) == 1 for _ in range(10))


def test_always_at_least_one():
    assert all(random_count(2.0) >= 1 for _ in range(50))
