import sys

from urban_dollop.cli._io import read_effects, write_rows
from urban_dollop.synth.supply_effects import supply_effects


def run(sigma=1.0):
    try:
        rows = read_effects("supply_effects.csv")
    except ValueError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
    write_rows(supply_effects(rows, sigma), "supply_effects.csv")
