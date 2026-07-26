import pandas as pd

from urban_dollop.synth.batch_sizes import batch_sizes


def run():
    full_primes, columns = batch_sizes()
    df = pd.DataFrame(columns, index=full_primes)
    df.index.name = "batch_size"
    df.to_csv("batch_size_distribution.csv")
