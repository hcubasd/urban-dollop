import tomllib
from pathlib import Path

from urban_dollop.cli.generate_demand import CLIError, require_file
from urban_dollop.freight_scheduling import FreightSchedulingConfig, schedule_freight
from urban_dollop.models.freight_trip import FreightTrip
from urban_dollop.models.freight_vehicle_params import FreightVehicleParams
from urban_dollop.models.shipment import Shipment

DEFAULT_OUTPUT_FILENAME = "freight_trips.csv"


def run_schedule_freight(input_dir: str, outdir: str | None = None) -> int:
    scenario_dir = Path(input_dir)
    if not scenario_dir.exists():
        raise CLIError(f"Input directory does not exist: {scenario_dir}")
    if not scenario_dir.is_dir():
        raise CLIError(f"Input path is not a directory: {scenario_dir}")

    output_path = _resolve_output_path(outdir)

    shipments_path = require_file(scenario_dir / "shipments.csv")
    vehicle_params_path = require_file(scenario_dir / "freight_vehicle_params.csv")

    config = FreightSchedulingConfig()
    config_path = Path.cwd() / "urban-dollop.toml"
    if config_path.exists():
        config = FreightSchedulingConfig.from_toml(config_path)

    try:
        shipments = Shipment.from_file(shipments_path)
        vehicle_params = FreightVehicleParams.from_file(vehicle_params_path)

        trips = schedule_freight(
            shipments=shipments,
            vehicle_params=vehicle_params,
            config=config,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise CLIError(str(exc)) from exc

    FreightTrip.to_file(trips, output_path)
    print(f"Wrote {len(trips)} freight trips to {output_path}")
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
