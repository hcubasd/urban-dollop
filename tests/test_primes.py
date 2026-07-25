from urban_dollop.helpers.primes import prime, primes


def test_primes_starts_with_one():
    assert primes(1) == [1]


def test_primes_sequence():
    assert primes(6) == [1, 2, 3, 5, 7, 11]


def test_prime_nth():
    assert prime(1) == 1
    assert prime(2) == 2
    assert prime(4) == 5
    assert prime(6) == 11
