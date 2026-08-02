from urban_dollop.helpers.distinct_values import distinct_values


def test_returns_n_distinct_sorted_values():
    values = distinct_values(5, sigma=1.0)
    assert len(values) == 5
    assert len(set(values)) == 5
    assert values == sorted(values)


def test_single_value_at_zero_sigma_is_deterministic():
    assert distinct_values(1, sigma=0.0) == [1]
