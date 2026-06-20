from pathlib import Path

import pytest

from urban_dollop import (
    Carrier,
    DeliveryTrip,
    Depot,
    ParcelSchedulingConfig,
    SkimMatrix,
    Vehicle,
    Zone,
    generate_parcel_demand,
    schedule_parcel_deliveries,
)

SCENARIO_DIR = Path(__file__).resolve().parent
FIXTURES_DIR = SCENARIO_DIR / "fixtures"


@pytest.fixture(autouse=True)
def chdir_to_scenario(monkeypatch):
    monkeypatch.chdir(SCENARIO_DIR)


def _load_fixtures():
    zones = Zone.from_file(FIXTURES_DIR / "zones.gpkg")
    depots = Depot.from_file(FIXTURES_DIR / "depots.gpkg")
    carriers = Carrier.from_file(FIXTURES_DIR / "carrier_shares.csv")
    vehicles = Vehicle.from_file(FIXTURES_DIR / "vehicles.csv")
    skim = SkimMatrix.from_file(FIXTURES_DIR / "skim_time.mtx", zones)
    return zones, depots, carriers, vehicles, skim


def test_schedule_parcel_deliveries_returns_stable_joinville_trips() -> None:
    zones, depots, carriers, vehicles, skim = _load_fixtures()
    demands = generate_parcel_demand(zones, depots, carriers, skim)

    trips = schedule_parcel_deliveries(
        demands, depots, vehicles, skim, ParcelSchedulingConfig(seed=42)
    )

    assert len(trips) == 393
    assert len({t.tour_id for t in trips}) == 138
    assert sum(t.n_parcels for t in trips) == 43995


def test_schedule_creates_return_legs() -> None:
    zones, depots, carriers, vehicles, skim = _load_fixtures()
    demands = generate_parcel_demand(zones, depots, carriers, skim)

    trips = schedule_parcel_deliveries(
        demands, depots, vehicles, skim, ParcelSchedulingConfig(seed=42)
    )

    n_tours = len({t.tour_id for t in trips})
    return_legs = [t for t in trips if t.n_parcels == 0]
    assert len(return_legs) == n_tours


def test_schedule_assigns_valid_vehicle_ids() -> None:
    zones, depots, carriers, vehicles, skim = _load_fixtures()
    demands = generate_parcel_demand(zones, depots, carriers, skim)
    valid_vehicle_ids = {v.vehicle_id for v in vehicles}

    trips = schedule_parcel_deliveries(
        demands, depots, vehicles, skim, ParcelSchedulingConfig(seed=42)
    )

    assert all(t.vehicle_id in valid_vehicle_ids for t in trips)


def test_schedule_trip_ids_are_sequential_per_tour() -> None:
    zones, depots, carriers, vehicles, skim = _load_fixtures()
    demands = generate_parcel_demand(zones, depots, carriers, skim)

    trips = schedule_parcel_deliveries(
        demands, depots, vehicles, skim, ParcelSchedulingConfig(seed=42)
    )

    from itertools import groupby

    for tour_id, tour_trips in groupby(trips, key=lambda t: t.tour_id):
        ids = [t.trip_id for t in tour_trips]
        assert ids == list(range(1, len(ids) + 1)), f"tour {tour_id}: {ids}"


def test_schedule_raises_for_depot_zone_not_in_skim() -> None:
    zones, depots, carriers, vehicles, skim = _load_fixtures()
    demands = generate_parcel_demand(zones, depots, carriers, skim)

    bad_depots = depots + [Depot(depot_id=99, carrier=carriers[0].name, zone_id=99999)]

    with pytest.raises(ValueError, match="zone_id.*not present in the skim"):
        schedule_parcel_deliveries(demands, bad_depots, vehicles, skim)


def test_vehicle_from_file_validates_max_parcels(tmp_path: Path) -> None:
    csv_path = tmp_path / "vehicles.csv"
    csv_path.write_text("vehicle_id,name,max_parcels\n1,van,-10\n", encoding="utf-8")

    with pytest.raises(Exception, match="max_parcels must be positive"):
        Vehicle.from_file(csv_path)


def test_delivery_trip_to_file_round_trips(tmp_path: Path) -> None:
    zones, depots, carriers, vehicles, skim = _load_fixtures()
    demands = generate_parcel_demand(zones, depots, carriers, skim)

    trips = schedule_parcel_deliveries(
        demands, depots, vehicles, skim, ParcelSchedulingConfig(seed=42)
    )

    out_path = tmp_path / "delivery_trips.csv"
    DeliveryTrip.to_file(trips, out_path)

    import pandas as pd

    df = pd.read_csv(out_path)
    expected_cols = list(DeliveryTrip.model_fields)
    assert list(df.columns) == expected_cols
    assert len(df) == len(trips)
