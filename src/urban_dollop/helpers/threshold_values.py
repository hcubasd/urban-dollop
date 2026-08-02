import random


def threshold_values(n_levels):
    """n_levels - 1 cutpoints (sorted ascending, Normal(0, 1), fixed
    regardless of --sigma) plus a trailing None -- the largest level always
    has no upper threshold. Textbook cumulative-logit cutpoints (McCullagh
    1980): n ordered levels need n-1 thresholds to partition the latent
    scale between them.
    """
    mus = sorted(random.normalvariate(0.0, 1.0) for _ in range(n_levels - 1))
    return mus + [None]
