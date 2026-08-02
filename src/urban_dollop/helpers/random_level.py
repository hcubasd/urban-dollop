from urban_dollop.helpers.random_count import random_count


def random_level(sigma):
    """A resource_level-like value: the same ceil(lognormal(0, sigma))
    shape as random_count, shifted down by one so it can be zero. Unlike a
    count of things to synthesize, a resource level legitimately starts at
    zero (the "none of this resource" outcome) and needs a real threshold
    between zero and whatever level comes next -- it isn't a count, even
    though it's drawn the same way one is. The shift is a constant
    translation, so it doesn't change the distribution's spread: as sigma
    grows, this value space widens exactly as random_count's does.
    """
    return random_count(sigma) - 1
