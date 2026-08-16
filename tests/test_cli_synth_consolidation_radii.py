import pandas as pd
import pytest

from urban_dollop.cli.synth_consolidation_radii import (
    consolidation_radii_need_synthesis,
    read_consolidation_radii,
)


def test_read_consolidation_radii_none_if_absent(tmp_path):
    assert read_consolidation_radii(str(tmp_path / "missing.csv")) is None


def test_read_consolidation_radii_shape_only(tmp_path):
    path = tmp_path / "consolidation_radii.csv"
    pd.DataFrame({"vehicle": ["van"], "resource": ["parcels"], "radius": [None]}).to_csv(path, index=False)
    pairs, complete = read_consolidation_radii(str(path))
    assert pairs == [{"vehicle": "van", "resource": "parcels"}]
    assert complete is False


def test_read_consolidation_radii_complete(tmp_path):
    path = tmp_path / "consolidation_radii.csv"
    pd.DataFrame({"vehicle": ["van"], "resource": ["parcels"], "radius": [1.5]}).to_csv(path, index=False)
    assert read_consolidation_radii(str(path))[1] is True


@pytest.mark.parametrize("radius", [0, -1])
def test_read_consolidation_radii_rejects_non_positive_values(tmp_path, radius):
    path = tmp_path / "bad.csv"
    pd.DataFrame({"vehicle": ["van"], "resource": ["parcels"], "radius": [radius]}).to_csv(path, index=False)
    with pytest.raises(ValueError):
        read_consolidation_radii(str(path))


def test_read_consolidation_radii_rejects_duplicate_pairs(tmp_path):
    path = tmp_path / "bad.csv"
    pd.DataFrame({
        "vehicle": ["van", "van"],
        "resource": ["parcels", "parcels"],
        "radius": [None, None],
    }).to_csv(path, index=False)
    with pytest.raises(ValueError):
        read_consolidation_radii(str(path))


def test_consolidation_radii_need_synthesis():
    assert consolidation_radii_need_synthesis(None) is True
    assert consolidation_radii_need_synthesis(([{"vehicle": "van", "resource": "parcels"}], False)) is True
    assert consolidation_radii_need_synthesis(([{"vehicle": "van", "resource": "parcels"}], True)) is False
