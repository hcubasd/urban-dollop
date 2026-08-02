import math
import random


def random_count(sigma=1.0):
    """How many of something to synthesize: ceil(lognormal(0, sigma)).
    Always >= 1, since lognormal support is strictly positive. The one place
    --sigma acts -- this is for counts, never for the values a count
    determines the quantity of."""
    return math.ceil(math.exp(random.normalvariate(0.0, sigma)))
