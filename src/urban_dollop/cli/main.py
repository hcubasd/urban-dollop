import argparse
import sys

from urban_dollop.cli.assign_network import run_assign_network
from urban_dollop.cli.consolidate_microhubs import run_consolidate_microhubs
from urban_dollop.cli.consolidate_uccs import run_consolidate_uccs
from urban_dollop.cli.generate_demand import CLIError, run_generate_demand
from urban_dollop.cli.schedule_deliveries import run_schedule_deliveries


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="urban-dollop",
        description="Run urban-dollop submodules from canonical scenario files.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate_demand = subparsers.add_parser(
        "generate-demand",
        help="Generate parcel demand from canonical input files.",
    )
    generate_demand.add_argument(
        "input_dir",
        help="Directory containing zones.gpkg, depots.gpkg, carrier_shares.csv, and skim_time.mtx.",
    )
    generate_demand.add_argument(
        "--outdir",
        help="Existing output directory or a .csv file path. Defaults to parcel_demand.csv in the current working directory.",
    )
    generate_demand.add_argument(
        "--logit",
        action="store_true",
        help="Use the ordered logit demand formulation instead of the linear formulation.",
    )
    generate_demand.set_defaults(
        handler=lambda args: run_generate_demand(
            args.input_dir, args.outdir, logit=args.logit
        )
    )

    schedule_deliveries = subparsers.add_parser(
        "schedule-deliveries",
        help="Schedule parcel deliveries into vehicle tours from canonical input files.",
    )
    schedule_deliveries.add_argument(
        "input_dir",
        help="Directory containing zones.gpkg, vehicles.csv, skim_distance.mtx, and parcel_demand.csv.",
    )
    schedule_deliveries.add_argument(
        "--outdir",
        help="Existing output directory or a .csv file path. Defaults to parcel_trips.csv in the current working directory.",
    )
    schedule_deliveries.set_defaults(
        handler=lambda args: run_schedule_deliveries(args.input_dir, args.outdir)
    )

    consolidate_microhubs_cmd = subparsers.add_parser(
        "consolidate-microhubs",
        help="Reroute zero-emission-zone parcels through microhubs.",
    )
    consolidate_microhubs_cmd.add_argument(
        "input_dir",
        help="Directory containing zones.gpkg, parcel_demand.csv, microhubs.csv, zero_emission_zones.csv, and skim_distance.mtx.",
    )
    consolidate_microhubs_cmd.add_argument(
        "--outdir",
        help="Existing output directory or a .csv file path. Defaults to parcel_demand.csv in the current working directory.",
    )
    consolidate_microhubs_cmd.set_defaults(
        handler=lambda args: run_consolidate_microhubs(args.input_dir, args.outdir)
    )

    consolidate_uccs_cmd = subparsers.add_parser(
        "consolidate-uccs",
        help="Reroute catchment-zone parcels through Urban Consolidation Centres.",
    )
    consolidate_uccs_cmd.add_argument(
        "input_dir",
        help="Directory containing zones.gpkg, parcel_demand.csv, uccs.csv, ucc_catchment_zones.csv, and skim_distance.mtx.",
    )
    consolidate_uccs_cmd.add_argument(
        "--outdir",
        help="Existing output directory or a .csv file path. Defaults to parcel_demand.csv in the current working directory.",
    )
    consolidate_uccs_cmd.set_defaults(
        handler=lambda args: run_consolidate_uccs(args.input_dir, args.outdir)
    )

    assign_network_cmd = subparsers.add_parser(
        "assign-network",
        help="Assign delivery trips to road network links via shortest-path routing.",
    )
    assign_network_cmd.add_argument(
        "input_dir",
        help="Directory containing one or more *_trips.csv files, network_links.gpkg (or .csv), zone_nodes.csv, and vehicles.csv.",
    )
    assign_network_cmd.add_argument(
        "--outdir",
        help="Existing output directory or a .csv file path. Defaults to loaded_links.csv in the current working directory.",
    )
    assign_network_cmd.set_defaults(
        handler=lambda args: run_assign_network(args.input_dir, args.outdir)
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        return args.handler(args)
    except CLIError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
