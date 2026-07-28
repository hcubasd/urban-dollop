import pandas as pd

from urban_dollop.synth.alternative_specific_constants import alternative_specific_constants


def run():
    pd.DataFrame(alternative_specific_constants()).to_csv("alternative_specific_constants.csv", index=False)
