import pandas as pd

from urban_dollop.synth.stratum_slopes import stratum_slopes


def run():
    pd.DataFrame(stratum_slopes()).to_csv("demand_slopes.csv", index=False)
