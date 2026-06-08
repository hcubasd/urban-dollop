import shutil
from pathlib import Path

import pandas as pd

from urban_dollop.cli.main import main

SCENARIO_DIR = Path(__file__).resolve().parent
FIXTURES_DIR = SCENARIO_DIR / "fixtures"


def test_generate_demand_writes_to_cwd_by_default(tmp_path: Path, monkeypatch) -> None:
    input_dir = tmp_path / "inputs"
    shutil.copytree(FIXTURES_DIR, input_dir)
    shutil.copy2(SCENARIO_DIR / "urban-dollop.toml", tmp_path)

    monkeypatch.chdir(tmp_path)
    exit_code = main(["generate-demand", "inputs"])

    assert exit_code == 0
    output_path = tmp_path / "parcel_demand.csv"
    assert output_path.exists()

    df = pd.read_csv(output_path)
    assert list(df.columns) == [
        "destination_zone_id",
        "depot_id",
        "n_parcels",
    ]
    assert len(df) > 0


def test_generate_demand_writes_to_outdir(tmp_path: Path, monkeypatch) -> None:
    input_dir = tmp_path / "scenario-data"
    shutil.copytree(FIXTURES_DIR, input_dir)
    shutil.copy2(SCENARIO_DIR / "urban-dollop.toml", tmp_path)

    monkeypatch.chdir(tmp_path)
    exit_code = main(["generate-demand", "--outdir", "scenario-data", "scenario-data"])

    assert exit_code == 0
    assert (input_dir / "parcel_demand.csv").exists()


def test_schedule_deliveries_writes_to_cwd_by_default(tmp_path: Path, monkeypatch) -> None:
    input_dir = tmp_path / "inputs"
    shutil.copytree(FIXTURES_DIR, input_dir)
    shutil.copy2(SCENARIO_DIR / "urban-dollop.toml", tmp_path)

    monkeypatch.chdir(tmp_path)
    main(["generate-demand", "inputs"])
    shutil.move(str(tmp_path / "parcel_demand.csv"), str(input_dir / "parcel_demand.csv"))

    exit_code = main(["schedule-deliveries", "inputs"])

    assert exit_code == 0
    output_path = tmp_path / "delivery_trips.csv"
    assert output_path.exists()

    df = pd.read_csv(output_path)
    assert list(df.columns) == [
        "tour_id",
        "trip_id",
        "depot_id",
        "carrier",
        "origin_zone_id",
        "destination_zone_id",
        "n_parcels",
        "vehicle_id",
    ]
    assert len(df) > 0
