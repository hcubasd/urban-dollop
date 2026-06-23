import tomllib
from pathlib import Path

from urban_dollop import (
    ParcelDemand,
    SkimDistance,
    UCC,
    UCCCatchmentZone,
    UCCConfig,
    Zone,
    consolidate_uccs,
)
from urban_dollop.cli.generate_demand import CLIError, require_file, require_spatial_file

DEFAULT_OUTPUT_FILENAME = "parcel_demand.csv"


def run_consolidate_uccs(input_dir: str, outdir: str | None = None) -> int:
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
    demand_path = require_file(scenario_dir / "parcel_demand.csv")
    uccs_path = require_file(scenario_dir / "uccs.csv")
    catchment_path = require_file(scenario_dir / "ucc_catchment_zones.csv")
    skim_dist_path = _require_skim_distance_file(scenario_dir)

    try:
        zones = Zone.from_file(zones_path)
        demands = ParcelDemand.from_file(demand_path)
        uccs = UCC.from_file(uccs_path)
        catchment_zones = UCCCatchmentZone.from_file(catchment_path)
        skim_distance = SkimDistance.from_file(skim_dist_path, zones)
        config = _load_ucc_config(config_path)
        result = consolidate_uccs(
            demands=demands,
            uccs=uccs,
            catchment_zones=catchment_zones,
            skim_distance=skim_distance,
            config=config,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise CLIError(str(exc)) from exc

    ParcelDemand.to_file(result, output_path)
    print(f"Wrote {len(result)} parcel demand rows to {output_path}")
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


def _load_ucc_config(path: Path) -> UCCConfig:
    with open(path, "rb") as f:
        data = tomllib.load(f).get("ucc_consolidation", {})
    return UCCConfig(**data)
