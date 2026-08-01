import pandas as pd

from urban_dollop.cli._sibling import borrow_resources, borrow_stratum_values
from urban_dollop.synth.slopes import random_strata, slopes


def run(sigma=1.0):
    zone_id = borrow_stratum_values("demand_slopes.csv", "zone_id")
    strata = random_strata(sigma, zone_id=zone_id)

    resources = borrow_resources("supply_thresholds.csv")
    if resources:
        strata["resource"] = resources

    pd.DataFrame(slopes(strata)).to_csv("supply_slopes.csv", index=False)
