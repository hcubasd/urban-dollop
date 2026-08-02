from urban_dollop.helpers.random_level import random_level


def test_zero_sigma_is_deterministic_zero():
    assert random_level(sigma=0.0) == 0


def test_never_negative():
    for _ in range(50):
        assert random_level(sigma=1.5) >= 0


def test_sometimes_zero_and_sometimes_positive():
    values = {random_level(sigma=1.0) for _ in range(200)}
    assert 0 in values
    assert any(v > 0 for v in values)
