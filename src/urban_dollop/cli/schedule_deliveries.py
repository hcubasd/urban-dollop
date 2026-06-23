import tomllib
from pathlib import Path

from urban_dollop import (
    DeliveryTrip,
    ParcelDemand,
    ParcelSchedulingConfig,
    SkimDistance,
    Vehicle,
    Zone,
    schedule_parcel_deliveries,
)
from urban_dollop.cli.generate_demand import CLIError, require_file

DEFAULT_OUTPUT_FILENAME = "delivery_trips.csv"


def run_schedule_deliveries(input_dir: str, outdir: str | None = None) -> int:
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
    zones_path = require_file(scenario_dir / "zones.gpkg")
    vehicles_path = require_file(scenario_dir / "vehicles.csv")
    skim_dist_path = _require_skim_distance_file(scenario_dir)
    demand_path = require_file(scenario_dir / "parcel_demand.csv")

    try:
        zones = Zone.from_file(zones_path)
        vehicles = Vehicle.from_file(vehicles_path)
        skim_distance = SkimDistance.from_file(skim_dist_path, zones)
        demands = ParcelDemand.from_file(demand_path)
        config = _load_scheduling_config(config_path)
        trips = schedule_parcel_deliveries(
            demands=demands,
            vehicles=vehicles,
            skim_distance=skim_distance,
            zones=zones,
            config=config,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise CLIError(str(exc)) from exc

    DeliveryTrip.to_file(trips, output_path)
    print(f"Wrote {len(trips)} delivery trip legs to {output_path}")
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


def _require_skim_distance_file(scenario_dir: Path) -> Path:
    for name in ("skim_distance.mtx", "skim_distance.mtx.gz"):
        p = scenario_dir / name
        if p.exists():
            return p
    raise CLIError(
        f"Missing required input file: {scenario_dir / 'skim_distance.mtx'} (or .gz)"
    )


def _load_scheduling_config(path: Path) -> ParcelSchedulingConfig:
    with open(path, "rb") as f:
        data = tomllib.load(f).get("parcel_scheduling", {})
    return ParcelSchedulingConfig(**data)
