"""urban-dollop — MASS-GT urban freight simulation as a Python package."""

from urban_dollop.models import Carrier, Depot, GeoEntity, ParcelDemand, SkimMatrix, Zone
from urban_dollop.parcel_demand import ParcelDemandConfig, generate_parcel_demand

__all__ = [
    "Zone", "Depot", "Carrier", "SkimMatrix", "ParcelDemand",
    "ParcelDemandConfig", "generate_parcel_demand",
]
