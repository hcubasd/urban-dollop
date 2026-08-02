import sys

from urban_dollop.cli._io import read_effects, write_rows
from urban_dollop.synth.need_effects import need_effects


def run(sigma=1.0):
    try:
        rows = read_effects("need_effects.csv")
    except ValueError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
    write_rows(need_effects(rows, sigma), "need_effects.csv")
