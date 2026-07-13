import tomllib
from pathlib import Path

from urban_dollop.cli.generate_demand import CLIError, require_file, require_spatial_file
from urban_dollop.freight_demand import FreightDemandConfig, generate_freight_demand
from urban_dollop.models.firm import Firm
from urban_dollop.models.freight_mnl_param import FreightMNLParam
from urban_dollop.models.freight_total import FreightTotal
from urban_dollop.models.freight_vehicle_params import FreightVehicleParams
from urban_dollop.models.make_use_coefficient import MakeUseCoefficient
from urban_dollop.models.shipment import Shipment
from urban_dollop.models.shipment_size_class import ShipmentSizeClass
from urban_dollop.models.skim_distance import SkimDistance
from urban_dollop.models.skim_matrix import SkimMatrix
from urban_dollop.models.zone import Zone

DEFAULT_OUTPUT_FILENAME = "shipments.csv"


def run_generate_freight_demand(input_dir: str, outdir: str | None = None) -> int:
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
    firms_path = require_file(scenario_dir / "firms.csv")
    freight_totals_path = require_file(scenario_dir / "freight_demand.csv")
    make_use_path = require_file(scenario_dir / "make_use_coefficients.csv")
    size_classes_path = require_file(scenario_dir / "shipment_size_classes.csv")
    vehicle_params_path = require_file(scenario_dir / "freight_vehicle_params.csv")
    mnl_params_path = require_file(scenario_dir / "freight_mnl_params.csv")
    skim_time_path = require_file(scenario_dir / "skim_time.mtx")
    skim_dist_path = require_file(scenario_dir / "skim_distance.mtx")

    config = _load_config(config_path)

    try:
        zones = Zone.from_file(zones_path)
        firms = Firm.from_file(firms_path)
        freight_totals = FreightTotal.from_file(freight_totals_path)
        make_use = MakeUseCoefficient.from_file(make_use_path)
        size_classes = ShipmentSizeClass.from_file(size_classes_path)
        vehicle_params = FreightVehicleParams.from_file(vehicle_params_path)
        mnl_params = FreightMNLParam.from_file(mnl_params_path)
        skim_time = SkimMatrix.from_file(skim_time_path, zones)
        skim_distance = SkimDistance.from_file(skim_dist_path, zones)

        shipments = generate_freight_demand(
            firms=firms,
            freight_totals=freight_totals,
            make_use=make_use,
            size_classes=size_classes,
            vehicle_params=vehicle_params,
            mnl_params=mnl_params,
            skim_time=skim_time,
            skim_distance=skim_distance,
            config=config,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise CLIError(str(exc)) from exc

    Shipment.to_file(shipments, output_path)
    print(f"Wrote {len(shipments)} shipments to {output_path}")
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


def _load_config(config_path: Path) -> FreightDemandConfig:
    with open(config_path, "rb") as f:
        data = tomllib.load(f).get("freight_demand", {})
    return FreightDemandConfig(**data)
