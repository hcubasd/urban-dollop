from pathlib import Path

from urban_dollop import (
    Microhub,
    ParcelDemand,
    SkimDistance,
    Zone,
    ZeroEmissionZone,
    consolidate_microhubs,
)
from urban_dollop.cli.generate_demand import CLIError, require_file

DEFAULT_OUTPUT_FILENAME = "parcel_demand.csv"


def run_consolidate_microhubs(input_dir: str, outdir: str | None = None) -> int:
    scenario_dir = Path(input_dir)
    if not scenario_dir.exists():
        raise CLIError(f"Input directory does not exist: {scenario_dir}")
    if not scenario_dir.is_dir():
        raise CLIError(f"Input path is not a directory: {scenario_dir}")

    output_path = _resolve_output_path(outdir)
    zones_path = require_file(scenario_dir / "zones.gpkg")
    demand_path = require_file(scenario_dir / "parcel_demand.csv")
    microhubs_path = require_file(scenario_dir / "microhubs.csv")
    zez_path = require_file(scenario_dir / "zero_emission_zones.csv")
    skim_dist_path = _require_skim_distance_file(scenario_dir)

    try:
        zones = Zone.from_file(zones_path)
        demands = ParcelDemand.from_file(demand_path)
        microhubs = Microhub.from_file(microhubs_path)
        zez_zones = ZeroEmissionZone.from_file(zez_path)
        skim_distance = SkimDistance.from_file(skim_dist_path, zones)
        result = consolidate_microhubs(
            demands=demands,
            microhubs=microhubs,
            zez_zones=zez_zones,
            skim_distance=skim_distance,
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
