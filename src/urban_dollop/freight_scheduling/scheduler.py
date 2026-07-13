import math
from collections import defaultdict

from urban_dollop.freight_scheduling.config import FreightSchedulingConfig
from urban_dollop.models.freight_trip import FreightTrip
from urban_dollop.models.freight_vehicle_params import FreightVehicleParams
from urban_dollop.models.shipment import Shipment


def schedule_freight(
    shipments: list[Shipment],
    vehicle_params: list[FreightVehicleParams],
    config: FreightSchedulingConfig | None = None,
) -> list[FreightTrip]:
    """Consolidate freight shipments into vehicle trips.

    Groups shipments by (origin_zone_id, destination_zone_id, vehicle_id) and
    fills vehicles to capacity.  The number of trips dispatched for each group
    is ceil(total_weight_kg / capacity_kg), so every kilogram of demand is
    covered by at least one vehicle.

    The vehicle_id on each shipment was already chosen by the MNL in
    generate_freight_demand, so no vehicle selection is performed here.

    Parameters
    ----------
    shipments:
        Output of generate_freight_demand().
    vehicle_params:
        Capacity parameters for each vehicle type; used to look up capacity_kg.
    config:
        Optional config; no parameters are currently used.
    """
    if not shipments:
        return []

    capacity = _build_capacity_lookup(shipments, vehicle_params)

    weight_by_group: dict[tuple[int, int, int], float] = defaultdict(float)
    for s in shipments:
        weight_by_group[(s.origin_zone_id, s.destination_zone_id, s.vehicle_id)] += s.weight_kg

    trips: list[FreightTrip] = []
    trip_id = 1

    for (orig, dest, veh_id), total_weight in weight_by_group.items():
        n_trips = math.ceil(total_weight / capacity[veh_id])
        for _ in range(n_trips):
            trips.append(FreightTrip(
                trip_id=trip_id,
                origin_zone_id=orig,
                destination_zone_id=dest,
                vehicle_id=veh_id,
            ))
            trip_id += 1

    return trips


def _build_capacity_lookup(
    shipments: list[Shipment],
    vehicle_params: list[FreightVehicleParams],
) -> dict[int, float]:
    capacity = {vp.vehicle_id: vp.capacity_kg for vp in vehicle_params}
    unknown = {s.vehicle_id for s in shipments} - capacity.keys()
    if unknown:
        raise ValueError(
            f"Shipments reference vehicle_id values not in freight_vehicle_params: "
            f"{sorted(unknown)}."
        )
    return capacity
