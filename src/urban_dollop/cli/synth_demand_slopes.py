import pandas as pd

from urban_dollop.cli._sibling import borrow_resources, borrow_stratum_values
from urban_dollop.synth.slopes import random_strata, slopes


def run(sigma=1.0):
    # zone_id: borrowed from the sibling slopes file if present -- supply
    # and demand share one geography, unlike the generic stratum_i
    # dimensions, which have no reason to correspond across the two sides.
    zone_id = borrow_stratum_values("supply_slopes.csv", "zone_id")
    strata = random_strata(sigma, zone_id=zone_id)

    # resource: borrowed (names only) from the same-side paired thresholds
    # file if present. If it doesn't exist yet, no resource stratum at all --
    # not an error, just the same "missing = 0" default used everywhere else.
    resources = borrow_resources("demand_thresholds.csv")
    if resources:
        strata["resource"] = resources

    pd.DataFrame(slopes(strata)).to_csv("demand_slopes.csv", index=False)
