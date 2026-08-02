from urban_dollop.helpers.random_subset import random_subset


def test_single_element_population_returns_that_element():
    assert random_subset([1]) == [1]


def test_never_empty():
    population = list(range(10))
    for _ in range(50):
        assert len(random_subset(population)) >= 1


def test_never_larger_than_population():
    population = list(range(10))
    for _ in range(50):
        assert len(random_subset(population)) <= len(population)


def test_result_is_a_subset_without_duplicates():
    population = list(range(10))
    for _ in range(50):
        subset = random_subset(population)
        assert len(subset) == len(set(subset))
        assert set(subset) <= set(population)


def test_size_is_sometimes_less_than_the_full_population():
    population = list(range(20))
    sizes = {len(random_subset(population)) for _ in range(200)}
    assert min(sizes) < len(population)
