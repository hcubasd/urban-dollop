from urban_dollop.helpers.truncated_draw import truncated_draw

PMF = [(0, 0.2), (1, 0.3), (2, 0.2), (5, 0.2), (10, 0.1)]


def test_infeasible_returns_none():
    assert truncated_draw([(5, 1.0)], budget=3) is None


def test_only_draws_values_within_budget():
    for _ in range(100):
        assert truncated_draw(PMF, budget=3) in (0, 1, 2)


def test_budget_at_least_max_reaches_every_level():
    draws = {truncated_draw(PMF, budget=100) for _ in range(300)}
    assert draws == {0, 1, 2, 5, 10}


def test_zero_budget_zero_level_draws_zero():
    assert truncated_draw([(0, 1.0)], budget=0) == 0


def test_zero_budget_no_zero_level_is_infeasible():
    assert truncated_draw([(1, 1.0)], budget=0) is None
