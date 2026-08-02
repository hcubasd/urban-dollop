import sys

from urban_dollop.cli._io import read_thresholds, write_rows
from urban_dollop.synth.supply_thresholds import supply_thresholds


def run(sigma=1.0):
    try:
        rows = read_thresholds("supply_thresholds.csv")
    except ValueError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
    write_rows(supply_thresholds(rows, sigma), "supply_thresholds.csv")
