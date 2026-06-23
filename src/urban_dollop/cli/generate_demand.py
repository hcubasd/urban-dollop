import tomllib
from pathlib import Path

from urban_dollop import (
    Carrier,
    Depot,
    LinearZone,
    LogitDemandConfig,
    LogitZone,
    ParcelDemand,
    ParcelDemandConfig,
    SkimMatrix,
    Zone,
    generate_logit_demand,
    generate_parcel_demand,
)

DEFAULT_OUTPUT_FILENAME = "parcel_demand.csv"


class CLIError(Exception):
    """Raised for user-facing CLI usage errors."""


def run_generate_demand(
    input_dir: str,
    outdir: str | None = None,
    logit: bool = False,
) -> int:
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
    zones_path = require_spatial_file(scenario_dir, "zones")
    depots_path = require_spatial_file(scenario_dir, "depots")
    carriers_path = require_file(scenario_dir / "carrier_shares.csv")
    skim_path = require_skim_file(scenario_dir)

    try:
        depots = Depot.from_file(depots_path)
        carriers = Carrier.from_file(carriers_path)

        if logit:
            zones = LogitZone.from_file(zones_path)
            skim = SkimMatrix.from_file(skim_path, zones)
            config = _load_logit_config(config_path)
            demands = generate_logit_demand(
                zones=zones,
                depots=depots,
                carriers=carriers,
                skim=skim,
                config=config,
            )
        else:
            zones = LinearZone.from_file(zones_path)
            skim = SkimMatrix.from_file(skim_path, zones)
            config = _load_linear_config(config_path)
            demands = generate_parcel_demand(
                zones=zones,
                depots=depots,
                carriers=carriers,
                skim=skim,
                config=config,
            )
    except (FileNotFoundError, ValueError) as exc:
        raise CLIError(str(exc)) from exc

    ParcelDemand.to_file(demands, output_path)
    print(f"Wrote {len(demands)} parcel demand rows to {output_path}")
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


def require_file(path: Path) -> Path:
    if not path.exists():
        raise CLIError(f"Missing required input file: {path}")
    if not path.is_file():
        raise CLIError(f"Expected a file but found something else: {path}")
    return path


def require_spatial_file(scenario_dir: Path, stem: str) -> Path:
    """Return the first of <stem>.gpkg or <stem>.csv that exists in scenario_dir."""
    for ext in (".gpkg", ".csv"):
        p = scenario_dir / f"{stem}{ext}"
        if p.exists():
            return p
    raise CLIError(
        f"Missing required input file: {scenario_dir / stem}.gpkg (or .csv)"
    )


def require_skim_file(scenario_dir: Path) -> Path:
    for name in ("skim_time.mtx", "skim_time.mtx.gz"):
        p = scenario_dir / name
        if p.exists():
            return p
    raise CLIError(
        f"Missing required input file: {scenario_dir / 'skim_time.mtx'} (or .gz)"
    )


def _load_linear_config(path: Path) -> ParcelDemandConfig:
    with open(path, "rb") as f:
        data = tomllib.load(f).get("parcel_demand", {})
    return ParcelDemandConfig(**data)


def _load_logit_config(path: Path) -> LogitDemandConfig:
    with open(path, "rb") as f:
        data = tomllib.load(f).get("parcel_demand_logit", {})
    return LogitDemandConfig(**data)
