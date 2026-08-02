import sys

from urban_dollop.cli._io import check_sigma_relevant, read_thresholds, write_rows
from urban_dollop.synth.capacity_thresholds import capacity_thresholds


def run(sigma=1.0, sigma_given=False):
    try:
        rows = read_thresholds("capacity_thresholds.csv")
        check_sigma_relevant(rows, sigma_given, "capacity_thresholds.csv")
    except ValueError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
    write_rows(capacity_thresholds(rows, sigma), "capacity_thresholds.csv")
