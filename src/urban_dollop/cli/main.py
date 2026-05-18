import argparse
import sys

from urban_dollop.cli.generate_demand import CLIError, run_generate_demand


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
    generate_demand.set_defaults(
        handler=lambda args: run_generate_demand(args.input_dir, args.outdir)
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
