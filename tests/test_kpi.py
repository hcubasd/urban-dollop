import pytest

from urban_dollop.kpi import calculate_kpis
from urban_dollop.models.delivery_trip import DeliveryTrip
from urban_dollop.models.freight_trip import FreightTrip
from urban_dollop.models.kpi import KPI
from urban_dollop.models.link_emission import LinkEmission
from urban_dollop.models.loaded_link import LoadedLink
from urban_dollop.models.network_link import NetworkLink
from urban_dollop.models.service_trip import ServiceTrip


def link(link_id=1, distance_m=1000.0, road_type="urban"):
    return NetworkLink(link_id=link_id, from_node_id=1, to_node_id=2,
                       distance_m=distance_m, road_type=road_type)


def loaded(link_id=1, vehicle_id=1, n_trips=1):
    return LoadedLink(link_id=link_id, vehicle_id=vehicle_id, n_trips=n_trips)


def emission(link_id=1, vehicle_id=1, pollutant="CO2", emission_g=100.0):
    return LinkEmission(link_id=link_id, vehicle_id=vehicle_id, hour=None,
                        pollutant=pollutant, emission_g=emission_g)


def parcel_trip(i=1):
    return DeliveryTrip(tour_id=1, trip_id=i, carrier="A",
                        origin_zone_id=1, destination_zone_id=2,
                        n_parcels=1, vehicle_id=1)


def freight_trip(i=1):
    return FreightTrip(trip_id=i, origin_zone_id=1, destination_zone_id=2, vehicle_id=1)


def service_trip(i=1):
    return ServiceTrip(trip_id=i, origin_zone_id=1, destination_zone_id=2, vehicle_id=1)


def run(**kwargs):
    defaults = dict(
        loaded_links=[loaded()],
        network_links=[link()],
        link_emissions=[emission()],
    )
    defaults.update(kwargs)
    return calculate_kpis(**defaults)


def kpi_value(kpis, indicator, dimension):
    for k in kpis:
        if k.indicator == indicator and k.dimension == dimension:
            return k.value
    raise KeyError(f"No KPI with indicator={indicator!r} dimension={dimension!r}")


# ── VKT ──────────────────────────────────────────────────────────────────────

def test_vkt_single_link_single_vehicle():
    kpis = run(
        loaded_links=[loaded(link_id=1, vehicle_id=1, n_trips=2)],
        network_links=[link(link_id=1, distance_m=500.0)],
    )
    assert kpi_value(kpis, "vkt", "vehicle_id=1") == pytest.approx(1.0)


def test_vkt_total_sums_all_vehicles():
    kpis = run(
        loaded_links=[
            loaded(link_id=1, vehicle_id=1, n_trips=1),
            loaded(link_id=1, vehicle_id=2, n_trips=1),
        ],
        network_links=[link(link_id=1, distance_m=2000.0)],
    )
    assert kpi_value(kpis, "vkt", "total") == pytest.approx(4.0)


def test_vkt_multiple_links_same_vehicle():
    kpis = run(
        loaded_links=[
            loaded(link_id=1, vehicle_id=1, n_trips=1),
            loaded(link_id=2, vehicle_id=1, n_trips=1),
        ],
        network_links=[
            link(link_id=1, distance_m=1000.0),
            link(link_id=2, distance_m=3000.0),
        ],
    )
    assert kpi_value(kpis, "vkt", "vehicle_id=1") == pytest.approx(4.0)


def test_vkt_unknown_link_raises():
    with pytest.raises(ValueError, match="link_id"):
        run(
            loaded_links=[loaded(link_id=99)],
            network_links=[link(link_id=1)],
        )


def test_vkt_empty_loaded_links():
    kpis = run(loaded_links=[], network_links=[link()])
    assert kpi_value(kpis, "vkt", "total") == 0.0


# ── emissions ─────────────────────────────────────────────────────────────────

def test_emissions_single_pollutant():
    kpis = run(link_emissions=[emission(pollutant="CO2", emission_g=500.0)])
    assert kpi_value(kpis, "emissions", "pollutant=CO2") == pytest.approx(500.0)


def test_emissions_summed_across_links():
    kpis = run(link_emissions=[
        emission(link_id=1, pollutant="CO2", emission_g=200.0),
        emission(link_id=2, pollutant="CO2", emission_g=300.0),
    ])
    assert kpi_value(kpis, "emissions", "pollutant=CO2") == pytest.approx(500.0)


def test_emissions_multiple_pollutants_independent():
    kpis = run(link_emissions=[
        emission(pollutant="CO2", emission_g=100.0),
        emission(pollutant="NOx", emission_g=50.0),
    ])
    assert kpi_value(kpis, "emissions", "pollutant=CO2") == pytest.approx(100.0)
    assert kpi_value(kpis, "emissions", "pollutant=NOx") == pytest.approx(50.0)


def test_emissions_empty():
    kpis = run(link_emissions=[])
    assert not any(k.indicator == "emissions" for k in kpis)


# ── trip counts ───────────────────────────────────────────────────────────────

def test_trip_count_all_none_gives_zeros():
    kpis = run()
    assert kpi_value(kpis, "trip_count", "type=parcel") == 0.0
    assert kpi_value(kpis, "trip_count", "type=freight") == 0.0
    assert kpi_value(kpis, "trip_count", "type=service") == 0.0
    assert kpi_value(kpis, "trip_count", "total") == 0.0


def test_trip_count_parcel():
    kpis = run(parcel_trips=[parcel_trip(1), parcel_trip(2)])
    assert kpi_value(kpis, "trip_count", "type=parcel") == 2.0


def test_trip_count_freight():
    kpis = run(freight_trips=[freight_trip(1), freight_trip(2), freight_trip(3)])
    assert kpi_value(kpis, "trip_count", "type=freight") == 3.0


def test_trip_count_service():
    kpis = run(service_trips=[service_trip(1)])
    assert kpi_value(kpis, "trip_count", "type=service") == 1.0


def test_trip_count_total_sums_all_types():
    kpis = run(
        parcel_trips=[parcel_trip(1)],
        freight_trips=[freight_trip(1), freight_trip(2)],
        service_trips=[service_trip(1)],
    )
    assert kpi_value(kpis, "trip_count", "total") == 4.0


# ── output structure ──────────────────────────────────────────────────────────

def test_output_is_list_of_kpi():
    kpis = run()
    assert all(isinstance(k, KPI) for k in kpis)


def test_all_kpis_have_non_empty_unit():
    kpis = run()
    assert all(k.unit for k in kpis)
