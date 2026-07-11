import tomllib
from pathlib import Path

from urban_dollop import DeliveryTrip, Vehicle
from urban_dollop.cli.generate_demand import CLIError, require_file, require_spatial_file
from urban_dollop.models.loaded_link import LoadedLink
from urban_dollop.models.network_link import NetworkLink
from urban_dollop.models.zone_node import ZoneNode
from urban_dollop.network_assignment import NetworkAssignmentConfig, assign_network

DEFAULT_OUTPUT_FILENAME = "loaded_links.csv"


def run_assign_network(input_dir: str, outdir: str | None = None) -> int:
    scenario_dir = Path(input_dir)
    if not scenario_dir.exists():
        raise CLIError(f"Input directory does not exist: {scenario_dir}")
    if not scenario_dir.is_dir():
        raise CLIError(f"Input path is not a directory: {scenario_dir}")

    config_path = Path.cwd() / "urban-dollop.toml"
    if not config_path.exists():
        raise CLIError(
            f"Missing configuration file: {config_path}. "
            "Run the command from the project root or place urban-dollop.toml in the current working directory."
        )

    output_path = _resolve_output_path(outdir)
    trip_files = _collect_trip_files(scenario_dir)
    links_path = _require_network_links_file(scenario_dir)
    zone_nodes_path = require_file(scenario_dir / "zone_nodes.csv")
    vehicles_path = require_file(scenario_dir / "vehicles.csv")

    try:
        trips = [t for f in trip_files for t in DeliveryTrip.from_file(f)]
        links = NetworkLink.from_file(links_path)
        zone_nodes = ZoneNode.from_file(zone_nodes_path)
        vehicles = Vehicle.from_file(vehicles_path)
        config = _load_config(config_path)
        result = assign_network(
            trips=trips,
            links=links,
            zone_nodes=zone_nodes,
            vehicles=vehicles,
            config=config,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise CLIError(str(exc)) from exc

    n_files = len(trip_files)
    LoadedLink.to_file(result, output_path)
    print(f"Loaded {len(trips)} trips from {n_files} file(s); wrote {len(result)} loaded link records to {output_path}")
    return 0


def _resolve_output_path(outdir: str | None) -> Path:
    if outdir is None:
        return Path.cwd() / DEFAULT_OUTPUT_FILENAME

    path = Path(outdir)
    if path.exists():
        if path.is_dir():
            return path / DEFAULT_OUTPUT_FILENAME
        return path

    if path.suffix.lower() == ".csv":
        if not path.parent.exists():
            raise CLIError(f"Output parent directory does not exist: {path.parent}")
        return path

    raise CLIError(
        f"Output path does not exist: {path}. "
        "Pass an existing directory or a .csv file path whose parent directory already exists."
    )


def _collect_trip_files(scenario_dir: Path) -> list[Path]:
    files = sorted(scenario_dir.glob("*_trips.csv"))
    if not files:
        raise CLIError(
            f"No *_trips.csv files found in {scenario_dir}. "
            "Run schedule-deliveries (or another scheduler) first."
        )
    return files


def _require_network_links_file(scenario_dir: Path) -> Path:
    for ext in (".gpkg", ".csv"):
        p = scenario_dir / f"network_links{ext}"
        if p.exists():
            return p
    raise CLIError(
        f"Missing required input file: {scenario_dir / 'network_links.gpkg'} (or .csv)"
    )


def _load_config(path: Path) -> NetworkAssignmentConfig:
    with open(path, "rb") as f:
        data = tomllib.load(f).get("network_assignment", {})
    return NetworkAssignmentConfig(**data)
