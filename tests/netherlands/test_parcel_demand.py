import shutil
from pathlib import Path

from urban_dollop import (
    Carrier,
    Depot,
    SkimMatrix,
    Zone,
    generate_parcel_demand,
)

SCENARIO_DIR = Path(__file__).resolve().parent
FIXTURES_DIR = SCENARIO_DIR / "fixtures"


def _load_fixtures():
    zones = Zone.from_file(FIXTURES_DIR / "zones.gpkg")
    depots = Depot.from_file(FIXTURES_DIR / "depots.gpkg")
    carriers = Carrier.from_file(FIXTURES_DIR / "carrier_shares.csv")
    skim = SkimMatrix.from_file(FIXTURES_DIR / "skim_time.mtx.gz", zones)
    return zones, depots, carriers, skim


def test_canonical_loaders_read_netherlands_fixture_contract(monkeypatch) -> None:
    monkeypatch.chdir(SCENARIO_DIR)
    zones, depots, carriers, skim = _load_fixtures()

    assert len(zones) == 5925
    assert len(depots) == 11
    assert len(carriers) == 7
    assert skim.n_zones == 5925


def test_generate_parcel_demand_returns_stable_netherlands_flows(monkeypatch) -> None:
    monkeypatch.chdir(SCENARIO_DIR)
    zones, depots, carriers, skim = _load_fixtures()

    demands = generate_parcel_demand(zones, depots, carriers, skim)

    assert len(demands) == 23309
    assert sum(d.n_parcels for d in demands) == 250768


def test_generate_demand_writes_to_cwd_by_default(tmp_path: Path, monkeypatch) -> None:
    from urban_dollop.cli.main import main

    input_dir = tmp_path / "inputs"
    shutil.copytree(FIXTURES_DIR, input_dir)
    shutil.copy2(SCENARIO_DIR / "urban-dollop.toml", tmp_path)

    monkeypatch.chdir(tmp_path)
    exit_code = main(["generate-demand", "inputs"])

    assert exit_code == 0
    assert (tmp_path / "parcel_demand.csv").exists()
