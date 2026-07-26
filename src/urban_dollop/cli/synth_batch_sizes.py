import pandas as pd

from urban_dollop.synth.batch_sizes import batch_sizes


def run():
    pd.DataFrame(batch_sizes()).to_csv("batch_sizes.csv", index=False)
