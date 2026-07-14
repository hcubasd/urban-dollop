import sys
from pathlib import Path

from urban_dollop.cli.generate_demand import CLIError
from urban_dollop.kpi import KPIConfig, calculate_kpis
from urban_dollop.models.delivery_trip import DeliveryTrip
from urban_dollop.models.freight_trip import FreightTrip
from urban_dollop.models.kpi import KPI
from urban_dollop.models.link_emission import LinkEmission
from urban_dollop.models.loaded_link import LoadedLink
from urban_dollop.models.network_link import NetworkLink
from urban_dollop.models.service_trip import ServiceTrip


def run_calculate_kpis(input_dir: str, outdir: str | None) -> int:
    data = Path(input_dir)

    loaded_links_path = data / "loaded_links.csv"
    emissions_path = data / "link_emissions.csv"

    for p in (loaded_links_path, emissions_path):
        if not p.exists():
            raise CLIError(f"Required file not found: {p}")

    network_path = data / "network_links.gpkg"
    if not network_path.exists():
        network_path = data / "network_links.csv"
    if not network_path.exists():
        raise CLIError(f"Required file not found: network_links.gpkg or network_links.csv in {data}")

    loaded_links = LoadedLink.from_file(loaded_links_path)
    network_links = NetworkLink.from_file(network_path)
    link_emissions = LinkEmission.from_file(emissions_path)

    parcel_trips = DeliveryTrip.from_file(data / "parcel_trips.csv") if (data / "parcel_trips.csv").exists() else None
    freight_trips = FreightTrip.from_file(data / "freight_trips.csv") if (data / "freight_trips.csv").exists() else None
    service_trips = ServiceTrip.from_file(data / "service_trips.csv") if (data / "service_trips.csv").exists() else None

    config_path = data / "urban-dollop.toml"
    config = KPIConfig.from_toml(config_path) if config_path.exists() else KPIConfig()

    kpis = calculate_kpis(
        loaded_links=loaded_links,
        network_links=network_links,
        link_emissions=link_emissions,
        parcel_trips=parcel_trips,
        freight_trips=freight_trips,
        service_trips=service_trips,
        config=config,
    )

    if outdir is None:
        out_path = Path("kpis.csv")
    else:
        out = Path(outdir)
        out_path = out / "kpis.csv" if out.is_dir() else out

    KPI.to_file(kpis, out_path)
    print(f"Wrote {len(kpis)} KPI rows to {out_path}", file=sys.stderr)
    return 0
