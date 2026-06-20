from pathlib import Path

import numpy as np
import pytest

from urban_dollop import (
    Carrier,
    Depot,
    ParcelDemandConfig,
    SkimMatrix,
    Zone,
    generate_parcel_demand,
)

SCENARIO_DIR = Path(__file__).resolve().parent
FIXTURES_DIR = SCENARIO_DIR / "fixtures"


@pytest.fixture(autouse=True)
def chdir_to_scenario(monkeypatch):
    monkeypatch.chdir(SCENARIO_DIR)


def test_generate_parcel_demand_returns_stable_joinville_flows() -> None:
    zones = Zone.from_file(FIXTURES_DIR / "zones.gpkg")
    depots = Depot.from_file(FIXTURES_DIR / "depots.gpkg")
    carriers = Carrier.from_file(FIXTURES_DIR / "carrier_shares.csv")
    skim = SkimMatrix.from_file(FIXTURES_DIR / "skim_time.mtx", zones)

    demands = generate_parcel_demand(zones, depots, carriers, skim)

    assert len(demands) == 255
    assert sum(d.n_parcels for d in demands) == 43995
    assert len({d.destination_zone_id for d in demands}) == 43


def test_generate_parcel_demand_programmatic_config_overrides_toml() -> None:
    zones = Zone.from_file(FIXTURES_DIR / "zones.gpkg")
    depots = Depot.from_file(FIXTURES_DIR / "depots.gpkg")
    carriers = Carrier.from_file(FIXTURES_DIR / "carrier_shares.csv")
    skim = SkimMatrix.from_file(FIXTURES_DIR / "skim_time.mtx", zones)

    demands = generate_parcel_demand(
        zones,
        depots,
        carriers,
        skim,
        ParcelDemandConfig(
            parcels_per_household=0.1,
            parcels_per_employee=0.0,
            delivery_success_b2c=1.0,
            delivery_success_b2b=1.0,
        ),
    )

    assert len(demands) == 253
    assert sum(d.n_parcels for d in demands) == 16067


def test_canonical_loaders_read_joinville_fixture_contract() -> None:
    zones = Zone.from_file(FIXTURES_DIR / "zones.gpkg")
    depots = Depot.from_file(FIXTURES_DIR / "depots.gpkg")
    carriers = Carrier.from_file(FIXTURES_DIR / "carrier_shares.csv")
    skim = SkimMatrix.from_file(FIXTURES_DIR / "skim_time.mtx", zones)

    assert len(zones) == 43
    assert min(z.zone_id for z in zones) == 1
    assert max(z.zone_id for z in zones) == 43
    assert len(depots) == 15
    assert len(carriers) == 6
    assert skim.n_zones == 43
    assert skim.get(zones[0].zone_id, zones[0].zone_id) >= 0


def test_carrier_loader_raises_for_missing_required_columns(tmp_path: Path) -> None:
    csv_path = tmp_path / "carrier_shares.csv"
    csv_path.write_text("name\nalpha\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Missing columns"):
        Carrier.from_file(csv_path)


def test_skim_matrix_loads_gz_transparently(tmp_path: Path) -> None:
    zones = Zone.from_file(FIXTURES_DIR / "zones.gpkg")
    skim_plain = SkimMatrix.from_file(FIXTURES_DIR / "skim_time.mtx", zones)

    import gzip as _gzip
    gz_path = tmp_path / "skim_time.mtx.gz"
    with open(FIXTURES_DIR / "skim_time.mtx", "rb") as src, _gzip.open(gz_path, "wb") as dst:
        dst.write(src.read())

    skim_gz = SkimMatrix.from_file(gz_path, zones)
    assert skim_gz.n_zones == skim_plain.n_zones
    assert float(skim_gz.data[1]) == float(skim_plain.data[1])


def test_skim_matrix_raises_for_invalid_shape(tmp_path: Path) -> None:
    zones = Zone.from_file(FIXTURES_DIR / "zones.gpkg")

    bad_skim_path = tmp_path / "bad_skim.mtx"
    np.array([1, 2, 3], dtype=np.int32).tofile(bad_skim_path)

    with pytest.raises(ValueError, match="Expected 43² = 1849 values"):
        SkimMatrix.from_file(bad_skim_path, zones)


def test_generate_parcel_demand_skips_carriers_without_depots() -> None:
    zones = Zone.from_file(FIXTURES_DIR / "zones.gpkg")
    depots = Depot.from_file(FIXTURES_DIR / "depots.gpkg")
    carriers = Carrier.from_file(FIXTURES_DIR / "carrier_shares.csv")
    skim = SkimMatrix.from_file(FIXTURES_DIR / "skim_time.mtx", zones)

    demands = generate_parcel_demand(
        zones,
        depots,
        carriers + [Carrier(name="ghost", share=0.0)],
        skim,
    )

    assert len(demands) == 255
    assert all(d.depot_id is not None for d in demands)


def test_generate_parcel_demand_raises_for_depot_zone_not_in_skim() -> None:
    zones = Zone.from_file(FIXTURES_DIR / "zones.gpkg")
    depots = Depot.from_file(FIXTURES_DIR / "depots.gpkg")
    carriers = Carrier.from_file(FIXTURES_DIR / "carrier_shares.csv")
    skim = SkimMatrix.from_file(FIXTURES_DIR / "skim_time.mtx", zones)

    bad_depots = depots + [Depot(depot_id=99, carrier=carriers[0].name, zone_id=99999)]

    with pytest.raises(ValueError, match="zone_id.*not present in the skim"):
        generate_parcel_demand(zones, bad_depots, carriers, skim)


def test_generate_parcel_demand_requires_carrier_shares_to_sum_to_one() -> None:
    zones = Zone.from_file(FIXTURES_DIR / "zones.gpkg")
    depots = Depot.from_file(FIXTURES_DIR / "depots.gpkg")
    carriers = Carrier.from_file(FIXTURES_DIR / "carrier_shares.csv")
    skim = SkimMatrix.from_file(FIXTURES_DIR / "skim_time.mtx", zones)

    invalid_carriers = [*carriers[:-1], Carrier(name=carriers[-1].name, share=0.03)]

    with pytest.raises(ValueError, match="Carrier shares must sum to 1.0"):
        generate_parcel_demand(zones, depots, invalid_carriers, skim)
