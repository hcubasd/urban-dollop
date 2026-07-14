from collections import defaultdict

from urban_dollop.kpi.config import KPIConfig
from urban_dollop.models.delivery_trip import DeliveryTrip
from urban_dollop.models.freight_trip import FreightTrip
from urban_dollop.models.kpi import KPI
from urban_dollop.models.link_emission import LinkEmission
from urban_dollop.models.loaded_link import LoadedLink
from urban_dollop.models.network_link import NetworkLink
from urban_dollop.models.service_trip import ServiceTrip


def calculate_kpis(
    loaded_links: list[LoadedLink],
    network_links: list[NetworkLink],
    link_emissions: list[LinkEmission],
    parcel_trips: list[DeliveryTrip] | None = None,
    freight_trips: list[FreightTrip] | None = None,
    service_trips: list[ServiceTrip] | None = None,
    config: KPIConfig | None = None,
) -> list[KPI]:
    """Aggregate simulation outputs into a flat list of KPI rows.

    Computes VKT per vehicle type and total, total emissions per pollutant,
    and trip counts per pipeline type and total.  All three trip lists are
    optional; absent pipelines contribute zero to the trip count.
    """
    kpis: list[KPI] = []

    kpis.extend(_vkt(loaded_links, network_links))
    kpis.extend(_emissions(link_emissions))
    kpis.extend(_trip_counts(parcel_trips, freight_trips, service_trips))

    return kpis


def _vkt(loaded_links: list[LoadedLink], network_links: list[NetworkLink]) -> list[KPI]:
    dist = {n.link_id: n.distance_m for n in network_links}
    unknown = {ll.link_id for ll in loaded_links} - dist.keys()
    if unknown:
        raise ValueError(
            f"loaded_links references link_id values not in network_links: {sorted(unknown)}."
        )

    vkt_by_vehicle: dict[int, float] = defaultdict(float)
    for ll in loaded_links:
        vkt_by_vehicle[ll.vehicle_id] += ll.n_trips * dist[ll.link_id] / 1000.0

    kpis = []
    total = 0.0
    for vehicle_id, vkt in sorted(vkt_by_vehicle.items()):
        kpis.append(KPI(indicator="vkt", dimension=f"vehicle_id={vehicle_id}", value=round(vkt, 3), unit="km"))
        total += vkt
    kpis.append(KPI(indicator="vkt", dimension="total", value=round(total, 3), unit="km"))
    return kpis


def _emissions(link_emissions: list[LinkEmission]) -> list[KPI]:
    by_pollutant: dict[str, float] = defaultdict(float)
    for le in link_emissions:
        by_pollutant[le.pollutant] += le.emission_g

    return [
        KPI(indicator="emissions", dimension=f"pollutant={p}", value=round(v, 3), unit="g")
        for p, v in sorted(by_pollutant.items())
    ]


def _trip_counts(
    parcel_trips: list[DeliveryTrip] | None,
    freight_trips: list[FreightTrip] | None,
    service_trips: list[ServiceTrip] | None,
) -> list[KPI]:
    counts = {
        "parcel": len(parcel_trips) if parcel_trips is not None else 0,
        "freight": len(freight_trips) if freight_trips is not None else 0,
        "service": len(service_trips) if service_trips is not None else 0,
    }
    kpis = [
        KPI(indicator="trip_count", dimension=f"type={t}", value=float(n), unit="trips")
        for t, n in counts.items()
    ]
    kpis.append(KPI(indicator="trip_count", dimension="total", value=float(sum(counts.values())), unit="trips"))
    return kpis
