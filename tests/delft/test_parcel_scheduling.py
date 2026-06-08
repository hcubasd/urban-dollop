from pathlib import Path

import pytest

from urban_dollop import (
    Carrier,
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


@pytest.mark.slow
def test_schedule_parcel_deliveries_returns_stable_delft_trips() -> None:
    zones, depots, carriers, vehicles, skim = _load_fixtures()
    demands = generate_parcel_demand(zones, depots, carriers, skim)

    trips = schedule_parcel_deliveries(
        demands, depots, vehicles, skim, ParcelSchedulingConfig(seed=42)
    )

    assert len(trips) == 9761
    assert len({t.tour_id for t in trips}) == 322
    assert sum(t.n_parcels for t in trips) == 89970


@pytest.mark.slow
def test_schedule_delft_return_legs_equal_tour_count() -> None:
    zones, depots, carriers, vehicles, skim = _load_fixtures()
    demands = generate_parcel_demand(zones, depots, carriers, skim)

    trips = schedule_parcel_deliveries(
        demands, depots, vehicles, skim, ParcelSchedulingConfig(seed=42)
    )

    n_tours = len({t.tour_id for t in trips})
    return_legs = [t for t in trips if t.n_parcels == 0]
    assert len(return_legs) == n_tours
