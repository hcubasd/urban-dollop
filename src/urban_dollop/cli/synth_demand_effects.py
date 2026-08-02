import sys

from urban_dollop.cli._io import read_effects, write_rows
from urban_dollop.synth.demand_effects import demand_effects


def run(sigma=1.0):
    try:
        rows = read_effects("demand_effects.csv")
    except ValueError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
    write_rows(demand_effects(rows, sigma), "demand_effects.csv")
