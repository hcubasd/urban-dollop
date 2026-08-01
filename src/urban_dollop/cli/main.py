import sys


def _parse_sigma(args):
    """Pull --sigma <float> out of args, wherever it appears. Defaults to
    1.0 -- the standard deviation fed to every count-sizing draw in a synth
    command (the values themselves stay fixed regardless). Not every synth
    command reads it yet (that lands as each module is migrated off
    Student's-t sizing) — passing it to one that doesn't is a silent no-op
    for now, not an error."""
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
    if args[:2] == ["synth", "supply-thresholds"]:
        from urban_dollop.cli.synth_supply_thresholds import run

        run(sigma)
    elif args[:2] == ["synth", "demand-thresholds"]:
        from urban_dollop.cli.synth_demand_thresholds import run

        run(sigma)
    elif args[:2] == ["synth", "supply-slopes"]:
        from urban_dollop.cli.synth_supply_slopes import run

        run(sigma)
    elif args[:2] == ["synth", "demand-slopes"]:
        from urban_dollop.cli.synth_demand_slopes import run

        run(sigma)
    elif args[:2] == ["synth", "supply"]:
        from urban_dollop.cli.synth_supply import run

        run()
    elif args[:2] == ["synth", "demand"]:
        from urban_dollop.cli.synth_demand import run

        run()
    elif args[:2] == ["synth", "batch-sizes"]:
        from urban_dollop.cli.synth_batch_sizes import run

        run()
    elif args[:2] == ["synth", "zones"]:
        from urban_dollop.cli.synth_zones import run

        run()
    elif args[:2] == ["synth", "agents"]:
        from urban_dollop.cli.synth_agents import run

        run()
    elif args[:2] == ["synth", "desire-lines"]:
        from urban_dollop.cli.synth_desire_lines import run

        run()
    elif args[:2] == ["synth", "network"]:
        from urban_dollop.cli.synth_network import run

        run()
    elif args[:2] == ["synth", "departures"]:
        from urban_dollop.cli.synth_departures import run

        run()
    elif args[:2] == ["synth", "dwell-times"]:
        from urban_dollop.cli.synth_dwell_times import run

        run()
    elif args[:2] == ["synth", "alternative-specific-constants"]:
        from urban_dollop.cli.synth_alternative_specific_constants import run

        run()
    elif args[:2] == ["synth", "vehicle-velocities"]:
        from urban_dollop.cli.synth_vehicle_velocities import run

        run()
    elif args[:2] == ["synth", "vehicle-capacities"]:
        from urban_dollop.cli.synth_vehicle_capacities import run

        run()
    elif args[:2] == ["synth", "road-capacities"]:
        from urban_dollop.cli.synth_road_capacities import run

        run()
    elif args[:2] == ["synth", "vehicles"]:
        from urban_dollop.cli.synth_vehicles import run

        run()
    elif args[:2] == ["synth", "time-intervals"]:
        from urban_dollop.cli.synth_time_intervals import run

        run()
    elif args[:2] == ["synth", "network-loads"]:
        from urban_dollop.cli.synth_network_loads import run

        run()
    elif args[:2] == ["synth", "copert-v-coefficients"]:
        from urban_dollop.cli.synth_copert_v_coefficients import run

        run()
    elif args[:2] == ["synth", "emission-factors"]:
        from urban_dollop.cli.synth_emission_factors import run

        run()
    elif args[:2] == ["synth", "network-emissions"]:
        from urban_dollop.cli.synth_network_emissions import run

        run()
    else:
        print(f"unknown command: {' '.join(args)}", file=sys.stderr)
        sys.exit(1)
