from urban_dollop.helpers.threshold_values import threshold_values


def test_single_level_has_no_threshold():
    assert threshold_values(1) == [None]


def test_n_levels_gives_n_minus_one_thresholds_plus_none():
    values = threshold_values(4)
    assert len(values) == 4
    assert values[-1] is None
    assert all(isinstance(v, float) for v in values[:-1])


def test_thresholds_are_sorted_ascending():
    values = threshold_values(6)
    mus = values[:-1]
    assert mus == sorted(mus)
