import pandas as pd

from urban_dollop.synth.emission_factors import emission_factors


def run():
    pd.DataFrame(emission_factors()).to_csv("emission_factors.csv", index=False)
