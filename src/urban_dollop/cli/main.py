import sys


def _parse_sigma(args):
    """Pull --sigma <float> out of args, wherever it appears. Defaults to
    1.0 -- the standard deviation fed to every count-sizing draw in a synth
    command (the values themselves stay fixed regardless). Also reports
    whether --sigma was actually typed, since a command whose target file
    already exists needs to distinguish "defaulted, fine" from "explicitly
    passed something that has nothing left to control"."""
    sigma = 1.0
    sigma_given = False
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
            sigma_given = True
            i += 2
        else:
            remaining.append(args[i])
            i += 1
    return sigma, sigma_given, remaining


def main():
    sigma, sigma_given, args = _parse_sigma(sys.argv[1:])
    command = args[:2]

    if command == ["synth", "zones"]:
        from urban_dollop.cli.synth_zones import run

        run(sigma, sigma_given)
    elif command == ["synth", "supply-effects"]:
        from urban_dollop.cli.synth_supply_effects import run

        run(sigma, sigma_given)
    elif command == ["synth", "demand-effects"]:
        from urban_dollop.cli.synth_demand_effects import run

        run(sigma, sigma_given)
    elif command == ["synth", "capacity-effects"]:
        from urban_dollop.cli.synth_capacity_effects import run

        run(sigma, sigma_given)
    elif command == ["synth", "need-effects"]:
        from urban_dollop.cli.synth_need_effects import run

        run(sigma, sigma_given)
    elif command == ["synth", "supply-thresholds"]:
        from urban_dollop.cli.synth_supply_thresholds import run

        run(sigma, sigma_given)
    elif command == ["synth", "demand-thresholds"]:
        from urban_dollop.cli.synth_demand_thresholds import run

        run(sigma, sigma_given)
    elif command == ["synth", "capacity-thresholds"]:
        from urban_dollop.cli.synth_capacity_thresholds import run

        run(sigma, sigma_given)
    elif command == ["synth", "need-thresholds"]:
        from urban_dollop.cli.synth_need_thresholds import run

        run(sigma, sigma_given)
    elif command == ["synth", "supply"]:
        from urban_dollop.cli.synth_supply import run

        run(sigma, sigma_given)
    elif command == ["synth", "demand"]:
        from urban_dollop.cli.synth_demand import run

        run(sigma, sigma_given)
    elif command == ["synth", "capacities"]:
        from urban_dollop.cli.synth_capacities import run

        run(sigma, sigma_given)
    elif command == ["synth", "needs"]:
        from urban_dollop.cli.synth_needs import run

        run(sigma, sigma_given)
    elif command == ["synth", "agents"]:
        from urban_dollop.cli.synth_agents import run

        run(sigma, sigma_given)
    elif command == ["synth", "desire-lines"]:
        from urban_dollop.cli.synth_desire_lines import run

        run(sigma, sigma_given)
    else:
        print(f"unknown command: {' '.join(args)}", file=sys.stderr)
        sys.exit(1)
