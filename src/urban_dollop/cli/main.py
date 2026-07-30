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
