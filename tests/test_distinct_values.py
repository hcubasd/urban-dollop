from urban_dollop.helpers.distinct_values import distinct_values


def test_returns_n_distinct_sorted_values():
    values = distinct_values(5)
    assert len(values) == 5
    assert len(set(values)) == 5
    assert values == sorted(values)


def test_single_value():
    values = distinct_values(1)
    assert len(values) == 1
