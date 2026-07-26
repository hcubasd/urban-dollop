from urban_dollop.synth.batch_sizes import batch_sizes


def test_returns_primes_and_columns():
    full_primes, columns = batch_sizes()
    assert isinstance(full_primes, list)
    assert isinstance(columns, dict)


def test_each_column_sums_to_one():
    full_primes, columns = batch_sizes()
    for resource, probs in columns.items():
        assert abs(sum(probs.values()) - 1.0) < 1e-10


def test_all_primes_present_in_each_column():
    full_primes, columns = batch_sizes()
    for resource, probs in columns.items():
        assert set(probs.keys()) == set(full_primes)


def test_probabilities_are_non_negative():
    full_primes, columns = batch_sizes()
    for resource, probs in columns.items():
        for p in probs.values():
            assert p >= 0.0


def test_resource_names_are_sequential():
    _, columns = batch_sizes()
    for i, name in enumerate(columns):
        assert name == f"resource_{i + 1}"
