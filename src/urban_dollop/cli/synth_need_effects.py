import sys

from urban_dollop.cli._io import check_sigma_relevant, effects_need_synthesis, read_effects, write_rows
from urban_dollop.synth.need_effects import need_effects


def run(sigma=1.0, sigma_given=False):
    try:
        rows = read_effects("need_effects.csv")
        check_sigma_relevant(rows, sigma_given, "need_effects.csv")
    except ValueError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
    if not effects_need_synthesis(rows):
        return
    write_rows(need_effects(rows, sigma), "need_effects.csv")
