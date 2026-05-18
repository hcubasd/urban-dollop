import shutil
from pathlib import Path

import pandas as pd

from urban_dollop.cli.main import main


def test_generate_demand_writes_to_cwd_by_default(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    scenario_dir = repo_root / "tests" / "joinville"
    fixtures_dir = scenario_dir / "fixtures"

    input_dir = tmp_path / "inputs"
    shutil.copytree(fixtures_dir, input_dir)
    shutil.copy2(scenario_dir / "urban-dollop.toml", tmp_path)

    monkeypatch.chdir(tmp_path)
    exit_code = main(["generate-demand", "inputs"])

    assert exit_code == 0
    output_path = tmp_path / "parcel_demand.csv"
    assert output_path.exists()

    df = pd.read_csv(output_path)
    assert list(df.columns) == [
        "destination_zone_id",
        "depot_id",
        "vehicle_type",
        "n_parcels",
    ]
    assert len(df) > 0

    captured = capsys.readouterr()
    assert "Wrote" in captured.out


def test_generate_demand_writes_to_outdir(tmp_path: Path, monkeypatch) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    scenario_dir = repo_root / "tests" / "joinville"
    fixtures_dir = scenario_dir / "fixtures"

    input_dir = tmp_path / "scenario-data"
    shutil.copytree(fixtures_dir, input_dir)
    shutil.copy2(scenario_dir / "urban-dollop.toml", tmp_path)

    monkeypatch.chdir(tmp_path)
    exit_code = main(["generate-demand", "--outdir", "scenario-data", "scenario-data"])

    assert exit_code == 0
    assert (input_dir / "parcel_demand.csv").exists()
