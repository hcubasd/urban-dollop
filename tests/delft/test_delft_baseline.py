import shutil
from pathlib import Path

import pytest

from urban_dollop import (
    Carrier,
    Depot,
    SkimMatrix,
    Zone,
    generate_parcel_demand,
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
    skim = SkimMatrix.from_file(FIXTURES_DIR / "skim_time.mtx", zones)
    return zones, depots, carriers, skim


def test_canonical_loaders_read_delft_fixture_contract() -> None:
    zones, depots, carriers, skim = _load_fixtures()

    assert len(zones) == 1792
    assert len(depots) == 16
    assert len(carriers) == 8
    assert skim.n_zones == 1792


def test_generate_parcel_demand_returns_stable_delft_flows() -> None:
    zones, depots, carriers, skim = _load_fixtures()

    demands = generate_parcel_demand(zones, depots, carriers, skim)

    assert sum(d.n_parcels for d in demands) == 89970
    assert len(demands) == 9439
    assert {d.vehicle_type for d in demands} == {7}


def test_generate_demand_writes_to_cwd_by_default(tmp_path: Path, monkeypatch) -> None:
    from urban_dollop.cli.main import main

    input_dir = tmp_path / "inputs"
    shutil.copytree(FIXTURES_DIR, input_dir)
    shutil.copy2(SCENARIO_DIR / "urban-dollop.toml", tmp_path)

    monkeypatch.chdir(tmp_path)
    exit_code = main(["generate-demand", "inputs"])

    assert exit_code == 0
    assert (tmp_path / "parcel_demand.csv").exists()
