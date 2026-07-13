import tomllib
from pathlib import Path

from urban_dollop.cli.generate_demand import CLIError, require_file
from urban_dollop.emission import EmissionCalculationConfig, calculate_emissions
from urban_dollop.models.emission_factor import EmissionFactor
from urban_dollop.models.link_emission import LinkEmission
from urban_dollop.models.loaded_link import LoadedLink
from urban_dollop.models.network_link import NetworkLink

DEFAULT_OUTPUT_FILENAME = "link_emissions.csv"


def run_calculate_emissions(input_dir: str, outdir: str | None = None) -> int:
    scenario_dir = Path(input_dir)
    if not scenario_dir.exists():
        raise CLIError(f"Input directory does not exist: {scenario_dir}")
    if not scenario_dir.is_dir():
        raise CLIError(f"Input path is not a directory: {scenario_dir}")

    config_path = Path.cwd() / "urban-dollop.toml"
    if not config_path.exists():
        raise CLIError(
            f"Missing configuration file: {config_path}. "
            "Run the command from the project root or place urban-dollop.toml "
            "in the current working directory."
        )

    output_path = _resolve_output_path(outdir)
    loaded_links_path = require_file(scenario_dir / "loaded_links.csv")
    emission_factors_path = require_file(scenario_dir / "emission_factors.csv")
    network_links_path = _require_network_links_file(scenario_dir)

    try:
        loaded_links = LoadedLink.from_file(loaded_links_path)
        emission_factors = EmissionFactor.from_file(emission_factors_path)
        network_links = NetworkLink.from_file(network_links_path)
        config = _load_config(config_path)
        result = calculate_emissions(
            loaded_links=loaded_links,
            emission_factors=emission_factors,
            network_links=network_links,
            config=config,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise CLIError(str(exc)) from exc

    LinkEmission.to_file(result, output_path)
    print(
        f"Loaded {len(loaded_links)} link records; "
        f"wrote {len(result)} emission records to {output_path}"
    )
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
            raise CLIError(
                f"Output parent directory does not exist: {path.parent}"
            )
        return path

    raise CLIError(
        f"Output path does not exist: {path}. "
        "Pass an existing directory or a .csv file path whose parent directory "
        "already exists."
    )


def _require_network_links_file(scenario_dir: Path) -> Path:
    for ext in (".gpkg", ".csv"):
        p = scenario_dir / f"network_links{ext}"
        if p.exists():
            return p
    raise CLIError(
        f"Missing required input file: {scenario_dir / 'network_links.gpkg'} (or .csv)"
    )


def _load_config(path: Path) -> EmissionCalculationConfig:
    with open(path, "rb") as f:
        data = tomllib.load(f).get("emission_calculation", {})
    return EmissionCalculationConfig(**data)
