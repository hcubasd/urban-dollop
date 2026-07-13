import tomllib
from pathlib import Path

from urban_dollop.cli.generate_demand import CLIError, require_file, require_spatial_file
from urban_dollop.models.service_trip import ServiceTrip
from urban_dollop.models.service_trip_rate import ServiceTripRate
from urban_dollop.models.service_vehicle_share import ServiceVehicleShare
from urban_dollop.models.skim_matrix import SkimMatrix
from urban_dollop.models.zone import Zone
from urban_dollop.models.zone_employment import ZoneEmployment
from urban_dollop.service_trips import ServiceTripConfig, generate_service_trips

DEFAULT_OUTPUT_FILENAME = "service_trips.csv"


def run_generate_service_trips(input_dir: str, outdir: str | None = None) -> int:
    scenario_dir = Path(input_dir)
    if not scenario_dir.exists():
        raise CLIError(f"Input directory does not exist: {scenario_dir}")
    if not scenario_dir.is_dir():
        raise CLIError(f"Input path is not a directory: {scenario_dir}")

    config_path = Path.cwd() / "urban-dollop.toml"
    if not config_path.exists():
        raise CLIError(
            f"Missing configuration file: {config_path}. "
            "Run from the project root or place urban-dollop.toml in the current directory."
        )

    output_path = _resolve_output_path(outdir)

    zones_path = require_spatial_file(scenario_dir, "zones")
    employment_path = require_file(scenario_dir / "zone_employment.csv")
    rates_path = require_file(scenario_dir / "service_trip_rates.csv")
    vehicle_shares_path = require_file(scenario_dir / "service_vehicle_shares.csv")
    skim_time_path = require_file(scenario_dir / "skim_time.mtx")

    config = _load_config(config_path)

    try:
        zones = Zone.from_file(zones_path)
        zone_employment = ZoneEmployment.from_file(employment_path)
        trip_rates = ServiceTripRate.from_file(rates_path)
        vehicle_shares = ServiceVehicleShare.from_file(vehicle_shares_path)
        skim_time = SkimMatrix.from_file(skim_time_path, zones)

        trips = generate_service_trips(
            zone_employment=zone_employment,
            trip_rates=trip_rates,
            vehicle_shares=vehicle_shares,
            skim_time=skim_time,
            config=config,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise CLIError(str(exc)) from exc

    ServiceTrip.to_file(trips, output_path)
    print(f"Wrote {len(trips)} service trips to {output_path}")
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


def _load_config(config_path: Path) -> ServiceTripConfig:
    with open(config_path, "rb") as f:
        data = tomllib.load(f).get("service_trips", {})
    return ServiceTripConfig(**data)
