import pandas as pd

from urban_dollop.synth.thresholds import random_resources, thresholds


def run(sigma=1.0):
    # Thresholds never borrows from a sibling -- supply and demand resource
    # sets are allowed to differ freely (excess supply or unmet demand is a
    # legitimate outcome, not an error), and reconciling them is deferred to
    # agent synthesis, later in the pipeline.
    resources = random_resources(sigma)
    pd.DataFrame(thresholds(resources)).to_csv("demand_thresholds.csv", index=False)
