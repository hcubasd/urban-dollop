import random


def random_subset(population):
    """A uniformly-random non-empty subset of `population`: size drawn
    uniform over [1, len(population)] (bounded selection from an already-
    fixed set, not invention of a new count -- deliberately not tied to
    --sigma, which only ever controls unbounded counts), then which
    members via random.sample (unbiased over every subset of that size).
    Never empty -- a resource with zero eligible rows would carry no
    information, no reason to include it as a column at all.
    """
    k = random.randint(1, len(population))
    return random.sample(population, k)
