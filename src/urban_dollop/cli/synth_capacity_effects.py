import sys

from urban_dollop.cli._io import read_effects, write_rows
from urban_dollop.synth.capacity_effects import capacity_effects


def run(sigma=1.0):
    try:
        rows = read_effects("capacity_effects.csv")
    except ValueError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
    write_rows(capacity_effects(rows, sigma), "capacity_effects.csv")
