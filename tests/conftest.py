import numpy as np
import pytest

from urban_dollop.models.carrier import Carrier
from urban_dollop.models.depot import Depot
from urban_dollop.models.skim_matrix import SkimMatrix
from urban_dollop.models.vehicle import Vehicle
from urban_dollop.models.zone import Zone
from urban_dollop.parcel_demand.config import ParcelDemandConfig


@pytest.fixture
def zones():
    return [
        Zone(zone_id=1, households=100, employment=50),
        Zone(zone_id=2, households=200, employment=0),
        Zone(zone_id=3, households=0, employment=150),
        Zone(zone_id=4, households=50, employment=25),
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
    data = np.array([
         0, 10, 20, 15,
        10,  0, 12,  8,
        20, 12,  0, 18,
        15,  8, 18,  0,
    ], dtype=np.float32)
    return SkimMatrix(data=data, zones=zones)


@pytest.fixture
def demand_config():
    return ParcelDemandConfig(
        parcels_per_household=0.1,
        parcels_per_employee=0.04,
        delivery_success_b2c=1.0,
        delivery_success_b2b=1.0,
    )
