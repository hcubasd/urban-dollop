import sys

from urban_dollop.cli._io import check_sigma_relevant, effects_need_synthesis, read_effects, write_rows
from urban_dollop.synth.demand_effects import demand_effects


def run(sigma=1.0, sigma_given=False):
    try:
        rows = read_effects("demand_effects.csv")
        check_sigma_relevant(rows, sigma_given, "demand_effects.csv")
    except ValueError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
    if not effects_need_synthesis(rows):
        return
    write_rows(demand_effects(rows, sigma), "demand_effects.csv")
