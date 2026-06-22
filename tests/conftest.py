import numpy as np
import pytest

from urban_dollop.models.carrier import Carrier
from urban_dollop.models.depot import Depot
from urban_dollop.models.linear_zone import LinearZone
from urban_dollop.models.logit_zone import LogitZone
from urban_dollop.models.skim_matrix import SkimMatrix
from urban_dollop.models.vehicle import Vehicle
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
    )
