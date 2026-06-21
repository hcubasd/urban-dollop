from urban_dollop.parcel_demand.generator import _allocate_by_share


def test_sum_equals_total():
    assert sum(_allocate_by_share(100, [0.6, 0.4])) == 100
    assert sum(_allocate_by_share(7, [0.5, 0.5])) == 7
    assert sum(_allocate_by_share(1, [0.33, 0.33, 0.34])) == 1
    assert sum(_allocate_by_share(0, [0.6, 0.4])) == 0


def test_length_matches_number_of_shares():
    assert len(_allocate_by_share(10, [0.5, 0.3, 0.2])) == 3


def test_all_values_non_negative():
    assert all(v >= 0 for v in _allocate_by_share(10, [0.1, 0.3, 0.6]))


def test_zero_share_receives_zero():
    result = _allocate_by_share(10, [1.0, 0.0])
    assert result[1] == 0


def test_full_share_receives_total():
    result = _allocate_by_share(10, [0.0, 1.0])
    assert result[1] == 10


def test_equal_shares_distribute_evenly():
    result = _allocate_by_share(10, [0.5, 0.5])
    assert sorted(result) == [5, 5]


def test_indivisible_total_distributed_without_loss():
    result = _allocate_by_share(10, [1/3, 1/3, 1/3])
    assert sum(result) == 10
    assert all(v in (3, 4) for v in result)
