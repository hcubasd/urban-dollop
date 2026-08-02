import sys

from urban_dollop.cli._io import read_thresholds, write_rows
from urban_dollop.synth.demand_thresholds import demand_thresholds


def run(sigma=1.0):
    try:
        rows = read_thresholds("demand_thresholds.csv")
    except ValueError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
    write_rows(demand_thresholds(rows, sigma), "demand_thresholds.csv")
