import numpy as np
import pytest

from urban_dollop.models.carrier import Carrier
from urban_dollop.models.emission_factor import EmissionFactor
from urban_dollop.models.network_link import NetworkLink
from urban_dollop.models.zone_node import ZoneNode
from urban_dollop.models.depot import Depot
from urban_dollop.models.linear_zone import LinearZone
from urban_dollop.models.loaded_link import LoadedLink
from urban_dollop.models.logit_zone import LogitZone
from urban_dollop.consolidation.ucc_config import UCCConfig
from urban_dollop.models.microhub import Microhub
from urban_dollop.models.parcel_demand import ParcelDemand
from urban_dollop.models.skim_distance import SkimDistance
from urban_dollop.models.skim_matrix import SkimMatrix
from urban_dollop.models.ucc import UCC
from urban_dollop.models.ucc_catchment_zone import UCCCatchmentZone
from urban_dollop.models.vehicle import Vehicle
from urban_dollop.models.zero_emission_zone import ZeroEmissionZone
from urban_dollop.parcel_demand.config import ParcelDemandConfig
from urban_dollop.parcel_demand.logit_config import LogitDemandConfig


@pytest.fixture
def zones():
    return [
        LinearZone(zone_id=1, households=100, employment=50),
        LinearZone(zone_id=2, households=200, employment=0),
        LinearZone(zone_id=3, households=0, employment=150),
        LinearZone(zone_id=4, households=50, employment=25),
    ]


@pytest.fixture
def depots():
    return [
        Depot(depot_id=1, carrier="alpha", zone_id=1),
        Depot(depot_id=2, carrier="alpha", zone_id=3),
        Depot(depot_id=3, carrier="beta", zone_id=2),
    ]


@pytest.fixture
def carriers():
    return [
        Carrier(name="alpha", share=0.6),
        Carrier(name="beta", share=0.4),
    ]


@pytest.fixture
def vehicles():
    return [
        Vehicle(vehicle_id=1, name="van", max_parcels=50),
        Vehicle(vehicle_id=2, name="truck", max_parcels=200),
    ]


@pytest.fixture
def skim(zones):
    # Travel times (minutes): symmetric, zero diagonal
    #       z1  z2  z3  z4
    data = np.array(
        [
            0,
            10,
            20,
            15,
            10,
            0,
            12,
            8,
            20,
            12,
            0,
            18,
            15,
            8,
            18,
            0,
        ],
        dtype=np.float32,
    )
    return SkimMatrix(data=data, zones=zones)


@pytest.fixture
def demand_config():
    return ParcelDemandConfig(
        parcels_per_household=0.1,
        parcels_per_employee=0.04,
        delivery_success_b2c=1.0,
        delivery_success_b2b=1.0,
    )


@pytest.fixture
def logit_zones():
    return [
        LogitZone(zone_id=1, population=250, urbanization_level=1),
        LogitZone(zone_id=2, population=500, urbanization_level=2),
        LogitZone(zone_id=3, population=80, urbanization_level=1),
        LogitZone(zone_id=4, population=120, urbanization_level=2),
    ]


@pytest.fixture
def logit_config():
    # 9 parcel levels → 8 thresholds; β slightly positive for urb=2
    return LogitDemandConfig(
        beta_urbanization={1: 0.0, 2: 0.5},
        mu_thresholds=[1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0],
        parcel_levels=[0, 1, 2, 3, 4, 5, 10, 15, 20],
        reference_period_days=60.0,
    )


@pytest.fixture
def skim_distance(zones):
    # Travel distances (km): symmetric, zero diagonal — same topology as skim
    #       z1  z2  z3  z4
    data = np.array(
        [0, 10, 20, 15, 10, 0, 12, 8, 20, 12, 0, 18, 15, 8, 18, 0],
        dtype=np.float32,
    )
    return SkimDistance(data=data, zones=zones)


@pytest.fixture
def zez_zones():
    # Zone 4 is the zero-emission zone
    return [ZeroEmissionZone(zone_id=4)]


@pytest.fixture
def microhubs():
    # Alpha has a hub in zone 1, beta has a hub in zone 2
    return [
        Microhub(microhub_id=1, zone_id=1, carrier="alpha"),
        Microhub(microhub_id=2, zone_id=2, carrier="beta"),
    ]


@pytest.fixture
def mixed_demands():
    # Zone 3 is outside ZEZ, zone 4 is inside ZEZ
    return [
        ParcelDemand(origin_zone_id=1, destination_zone_id=3, carrier="alpha", n_parcels=10),
        ParcelDemand(origin_zone_id=1, destination_zone_id=4, carrier="alpha", n_parcels=5),
        ParcelDemand(origin_zone_id=2, destination_zone_id=4, carrier="beta", n_parcels=8),
    ]


@pytest.fixture
def ucc_catchment_zones():
    # Zones 3 and 4 are in the UCC catchment
    return [UCCCatchmentZone(zone_id=3), UCCCatchmentZone(zone_id=4)]


@pytest.fixture
def uccs():
    # Two UCCs: one at zone 1, one at zone 2
    return [UCC(ucc_id=1, zone_id=1), UCC(ucc_id=2, zone_id=2)]


@pytest.fixture
def ucc_config():
    return UCCConfig(probability=1.0)


@pytest.fixture
def network_links():
    # 5-node network:
    #   1 --10m--> 2 --15m--> 3
    #   1 --50m-------------- 3  (direct, longer)
    #   3 --8m--> 4
    #   2 --30m-------------- 4
    return [
        NetworkLink(link_id=1, from_node_id=1, to_node_id=2, distance_m=10.0, road_type="urban"),
        NetworkLink(link_id=2, from_node_id=2, to_node_id=3, distance_m=15.0, road_type="urban"),
        NetworkLink(link_id=3, from_node_id=1, to_node_id=3, distance_m=50.0, road_type="highway"),
        NetworkLink(link_id=4, from_node_id=3, to_node_id=4, distance_m=8.0,  road_type="rural"),
        NetworkLink(link_id=5, from_node_id=2, to_node_id=4, distance_m=30.0, road_type="rural"),
    ]


@pytest.fixture
def network_links_with_grade():
    return [
        NetworkLink(link_id=1, from_node_id=1, to_node_id=2, distance_m=10.0, road_type="urban", grade_pct=5.0),
        NetworkLink(link_id=2, from_node_id=2, to_node_id=3, distance_m=15.0, road_type="urban", grade_pct=2.0),
        NetworkLink(link_id=3, from_node_id=3, to_node_id=4, distance_m=8.0,  road_type="rural", grade_pct=0.0),
    ]


@pytest.fixture
def zone_nodes():
    # Each zone maps directly to the node with the same ID
    return [
        ZoneNode(zone_id=1, node_id=1),
        ZoneNode(zone_id=2, node_id=2),
        ZoneNode(zone_id=3, node_id=3),
        ZoneNode(zone_id=4, node_id=4),
    ]


def _make_ef(vehicle_id, pollutant, gradient_pct, load_pct, gamma):
    """Constant-rate emission factor (EF = gamma g/km regardless of speed)."""
    return EmissionFactor(
        vehicle_id=vehicle_id,
        pollutant=pollutant,
        gradient_pct=gradient_pct,
        load_pct=load_pct,
        alpha=0.0, beta=0.0, gamma=gamma,
        delta=0.0, epsilon=0.0, zeta=0.0,
        eta=1.0, rf=0.0,
    )


@pytest.fixture
def emission_factors():
    # Vehicle 1, CO2: 2×2 grid (gradient 0/2, load 0/100)
    # EF values chosen so bilinear interpolation is easy to verify:
    #   grad=0, load=0   → 100 g/km
    #   grad=0, load=100 → 200 g/km
    #   grad=2, load=0   → 150 g/km
    #   grad=2, load=100 → 300 g/km
    return [
        _make_ef(1, "CO2", 0.0, 0.0, 100.0),
        _make_ef(1, "CO2", 0.0, 100.0, 200.0),
        _make_ef(1, "CO2", 2.0, 0.0, 150.0),
        _make_ef(1, "CO2", 2.0, 100.0, 300.0),
    ]


@pytest.fixture
def network_links_simple():
    return [
        NetworkLink(link_id=1, from_node_id=1, to_node_id=2, distance_m=1000.0, road_type="urban", grade_pct=0.0),
    ]


@pytest.fixture
def loaded_links_simple():
    return [
        LoadedLink(link_id=1, vehicle_id=1, n_trips=1),
    ]


@pytest.fixture
def catchment_demands():
    # Zone 1 is outside catchment; zones 3 and 4 are inside
    return [
        ParcelDemand(origin_zone_id=1, destination_zone_id=1, carrier="alpha", n_parcels=10),
        ParcelDemand(origin_zone_id=1, destination_zone_id=3, carrier="alpha", n_parcels=8),
        ParcelDemand(origin_zone_id=2, destination_zone_id=4, carrier="beta", n_parcels=6),
    ]
