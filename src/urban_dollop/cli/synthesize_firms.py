import tomllib
from pathlib import Path

import geopandas as gpd

from urban_dollop import (
    Firm,
    FirmSizeClass,
    FirmSynthesisConfig,
    Zone,
    ZoneEmployment,
    synthesize_firms,
)
from urban_dollop.cli.generate_demand import CLIError, require_file, require_spatial_file

DEFAULT_OUTPUT_FILENAME = "firms.csv"


def run_synthesize_firms(input_dir: str, outdir: str | None = None) -> int:
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
    employment_path = require_file(scenario_dir / "zone_employment.csv")
    size_classes_path = require_file(scenario_dir / "firm_size_distribution.csv")

    config = _load_config(config_path)

    try:
        zones = Zone.from_file(zones_path)
        zone_employment = ZoneEmployment.from_file(employment_path)
        firm_size_classes = FirmSizeClass.from_file(size_classes_path)

        zone_polygons = None
        if zones_path.suffix.lower() in (".gpkg", ".shp"):
            gdf = gpd.read_file(zones_path)
            if "zone_id" in gdf.columns:
                zone_polygons = {
                    int(row["zone_id"]): row["geometry"]
                    for _, row in gdf[["zone_id", "geometry"]].iterrows()
                    if row["geometry"] is not None
                }

        firms = synthesize_firms(
            zones=zones,
            zone_employment=zone_employment,
            firm_size_classes=firm_size_classes,
            config=config,
            zone_polygons=zone_polygons,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise CLIError(str(exc)) from exc

    Firm.to_file(firms, output_path)
    print(f"Wrote {len(firms)} firms to {output_path}")
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


def _load_config(config_path: Path) -> FirmSynthesisConfig:
    with open(config_path, "rb") as f:
        data = tomllib.load(f).get("firm_synthesis", {})
    return FirmSynthesisConfig(**data)
