import pandas as pd
import pytest

from urban_dollop.cli.synth_alternative_specific_constants import (
    read_alternative_specific_constants,
    alternative_specific_constants_need_synthesis,
)


def test_read_alternative_specific_constants_none_if_absent(tmp_path):
    assert read_alternative_specific_constants(str(tmp_path / "missing.csv")) is None


def test_read_alternative_specific_constants_shape_only(tmp_path):
    path = tmp_path / "alternative_specific_constants.csv"
    pd.DataFrame({
        "vehicle": ["truck", "van"],
        "resource": ["grains", "parcels"],
        "alternative_specific_constant": [None, None],
    }).to_csv(path, index=False)
    pairs, complete = read_alternative_specific_constants(str(path))
    assert pairs == [
        {"vehicle": "truck", "resource": "grains"},
        {"vehicle": "van", "resource": "parcels"},
    ]
    assert complete is False


def test_read_alternative_specific_constants_complete(tmp_path):
    path = tmp_path / "alternative_specific_constants.csv"
    pd.DataFrame({
        "vehicle": ["truck"],
        "resource": ["grains"],
        "alternative_specific_constant": [-0.5],
    }).to_csv(path, index=False)
    pairs, complete = read_alternative_specific_constants(str(path))
    assert complete is True


def test_read_alternative_specific_constants_missing_column_rejected(tmp_path):
    path = tmp_path / "bad.csv"
    pd.DataFrame({"vehicle": ["truck"], "resource": ["grains"]}).to_csv(path, index=False)
    with pytest.raises(ValueError):
        read_alternative_specific_constants(str(path))


def test_read_alternative_specific_constants_duplicate_pairs_rejected(tmp_path):
    path = tmp_path / "bad.csv"
    pd.DataFrame({
        "vehicle": ["truck", "truck"],
        "resource": ["grains", "grains"],
        "alternative_specific_constant": [None, None],
    }).to_csv(path, index=False)
    with pytest.raises(ValueError):
        read_alternative_specific_constants(str(path))


def test_read_alternative_specific_constants_mixed_rejected(tmp_path):
    path = tmp_path / "bad.csv"
    pd.DataFrame({
        "vehicle": ["truck", "van"],
        "resource": ["grains", "parcels"],
        "alternative_specific_constant": [-0.5, None],
    }).to_csv(path, index=False)
    with pytest.raises(ValueError):
        read_alternative_specific_constants(str(path))


def test_alternative_specific_constants_need_synthesis_true_when_absent():
    assert alternative_specific_constants_need_synthesis(None) is True


def test_alternative_specific_constants_need_synthesis_true_when_shape_only():
    assert alternative_specific_constants_need_synthesis(([{"vehicle": "a", "resource": "b"}], False)) is True


def test_alternative_specific_constants_need_synthesis_false_when_complete():
    assert alternative_specific_constants_need_synthesis(([{"vehicle": "a", "resource": "b"}], True)) is False
