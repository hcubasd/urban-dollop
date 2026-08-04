import pandas as pd
import pytest

from urban_dollop.cli.synth_vehicle_velocities import read_vehicle_velocities, vehicle_velocities_need_synthesis


def test_read_vehicle_velocities_none_if_absent(tmp_path):
    assert read_vehicle_velocities(str(tmp_path / "missing.csv")) is None


def test_read_vehicle_velocities_shape_only(tmp_path):
    path = tmp_path / "vehicle_velocities.csv"
    pd.DataFrame({
        "vehicle": ["truck", "bike"],
        "road_type": ["highway", "residential"],
        "velocity": [None, None],
    }).to_csv(path, index=False)
    pairs, complete = read_vehicle_velocities(str(path))
    assert pairs == [
        {"vehicle": "truck", "road_type": "highway"},
        {"vehicle": "bike", "road_type": "residential"},
    ]
    assert complete is False


def test_read_vehicle_velocities_complete(tmp_path):
    path = tmp_path / "vehicle_velocities.csv"
    pd.DataFrame({"vehicle": ["truck"], "road_type": ["highway"], "velocity": [40.0]}).to_csv(path, index=False)
    pairs, complete = read_vehicle_velocities(str(path))
    assert complete is True


def test_read_vehicle_velocities_missing_column_rejected(tmp_path):
    path = tmp_path / "bad.csv"
    pd.DataFrame({"vehicle": ["truck"], "road_type": ["highway"]}).to_csv(path, index=False)
    with pytest.raises(ValueError):
        read_vehicle_velocities(str(path))


def test_read_vehicle_velocities_duplicate_pairs_rejected(tmp_path):
    path = tmp_path / "bad.csv"
    pd.DataFrame({
        "vehicle": ["truck", "truck"],
        "road_type": ["highway", "highway"],
        "velocity": [None, None],
    }).to_csv(path, index=False)
    with pytest.raises(ValueError):
        read_vehicle_velocities(str(path))


def test_read_vehicle_velocities_mixed_velocity_rejected(tmp_path):
    path = tmp_path / "bad.csv"
    pd.DataFrame({
        "vehicle": ["truck", "bike"],
        "road_type": ["highway", "residential"],
        "velocity": [40.0, None],
    }).to_csv(path, index=False)
    with pytest.raises(ValueError):
        read_vehicle_velocities(str(path))


def test_vehicle_velocities_need_synthesis_true_when_absent():
    assert vehicle_velocities_need_synthesis(None) is True


def test_vehicle_velocities_need_synthesis_true_when_shape_only():
    assert vehicle_velocities_need_synthesis(([{"vehicle": "a", "road_type": "b"}], False)) is True


def test_vehicle_velocities_need_synthesis_false_when_complete():
    assert vehicle_velocities_need_synthesis(([{"vehicle": "a", "road_type": "b"}], True)) is False
