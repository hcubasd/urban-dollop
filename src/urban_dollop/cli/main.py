import sys


def main():
    args = sys.argv[1:]
    if args[:2] == ["synth", "supply-thresholds"]:
        from urban_dollop.cli.synth_supply_thresholds import run

        run()
    elif args[:2] == ["synth", "demand-thresholds"]:
        from urban_dollop.cli.synth_demand_thresholds import run

        run()
    elif args[:2] == ["synth", "supply-slopes"]:
        from urban_dollop.cli.synth_supply_slopes import run

        run()
    elif args[:2] == ["synth", "demand-slopes"]:
        from urban_dollop.cli.synth_demand_slopes import run

        run()
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
    else:
        print(f"unknown command: {' '.join(args)}", file=sys.stderr)
        sys.exit(1)
