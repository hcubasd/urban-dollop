import sys

from urban_dollop.cli._io import check_sigma_relevant, effects_need_synthesis, read_effects, write_rows
from urban_dollop.synth.capacity_effects import capacity_effects


def run(sigma=1.0, sigma_given=False):
    try:
        rows = read_effects("capacity_effects.csv")
        check_sigma_relevant(rows, sigma_given, "capacity_effects.csv")
    except ValueError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
    if not effects_need_synthesis(rows):
        return
    write_rows(capacity_effects(rows, sigma), "capacity_effects.csv")
