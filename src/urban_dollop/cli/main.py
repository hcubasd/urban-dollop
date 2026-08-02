import sys


def _parse_sigma(args):
    """Pull --sigma <float> out of args, wherever it appears. Defaults to
    1.0 -- the standard deviation fed to every count-sizing draw in a synth
    command (the values themselves stay fixed regardless)."""
    sigma = 1.0
    remaining = []
    i = 0
    while i < len(args):
        if args[i] == "--sigma":
            if i + 1 >= len(args):
                print("--sigma requires a value", file=sys.stderr)
                sys.exit(1)
            try:
                sigma = float(args[i + 1])
            except ValueError:
                print(f"--sigma must be a number, got {args[i + 1]!r}", file=sys.stderr)
                sys.exit(1)
            if sigma < 0:
                print(f"--sigma must be >= 0, got {sigma}", file=sys.stderr)
                sys.exit(1)
            i += 2
        else:
            remaining.append(args[i])
            i += 1
    return sigma, remaining


def main():
    sigma, args = _parse_sigma(sys.argv[1:])
    command = args[:2]

    if command == ["synth", "supply-effects"]:
        from urban_dollop.cli.synth_supply_effects import run

        run(sigma)
    elif command == ["synth", "demand-effects"]:
        from urban_dollop.cli.synth_demand_effects import run

        run(sigma)
    elif command == ["synth", "capacity-effects"]:
        from urban_dollop.cli.synth_capacity_effects import run

        run(sigma)
    elif command == ["synth", "need-effects"]:
        from urban_dollop.cli.synth_need_effects import run

        run(sigma)
    elif command == ["synth", "supply-thresholds"]:
        from urban_dollop.cli.synth_supply_thresholds import run

        run(sigma)
    elif command == ["synth", "demand-thresholds"]:
        from urban_dollop.cli.synth_demand_thresholds import run

        run(sigma)
    elif command == ["synth", "capacity-thresholds"]:
        from urban_dollop.cli.synth_capacity_thresholds import run

        run(sigma)
    elif command == ["synth", "need-thresholds"]:
        from urban_dollop.cli.synth_need_thresholds import run

        run(sigma)
    else:
        print(f"unknown command: {' '.join(args)}", file=sys.stderr)
        sys.exit(1)
