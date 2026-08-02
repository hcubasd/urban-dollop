import sys

from urban_dollop.cli._io import check_sigma_relevant, read_thresholds, write_rows
from urban_dollop.synth.demand_thresholds import demand_thresholds


def run(sigma=1.0, sigma_given=False):
    try:
        rows = read_thresholds("demand_thresholds.csv")
        check_sigma_relevant(rows, sigma_given, "demand_thresholds.csv")
    except ValueError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
    write_rows(demand_thresholds(rows, sigma), "demand_thresholds.csv")
