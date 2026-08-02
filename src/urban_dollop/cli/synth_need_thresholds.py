import sys

from urban_dollop.cli._io import read_thresholds, write_rows
from urban_dollop.synth.need_thresholds import need_thresholds


def run(sigma=1.0):
    try:
        rows = read_thresholds("need_thresholds.csv")
    except ValueError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
    write_rows(need_thresholds(rows, sigma), "need_thresholds.csv")
