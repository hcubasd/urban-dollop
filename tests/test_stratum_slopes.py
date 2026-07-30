import math

import pytest

from urban_dollop.synth.stratum_slopes import stratum_slopes


def _group_by_dims(rows):
    dims = [k for k in rows[0] if k != "slope"]
    unique_values = {d: sorted(set(row[d] for row in rows)) for d in dims}
    return dims, unique_values


@pytest.fixture(scope="module")
def rows():
    for _ in range(20):
        result = stratum_slopes()
        if len(result) <= 500:
            return result
    pytest.skip("could not get a small draw after 20 attempts")


def test_returns_list_of_rows(rows):
    assert isinstance(rows, list)
    assert len(rows) >= 1


def test_rows_have_slope(rows):
    for row in rows:
        assert "slope" in row
        assert isinstance(row["slope"], float)


def test_stratum_values_are_strings(rows):
    dims, _ = _group_by_dims(rows)
    for row in rows:
        for d in dims:
            assert isinstance(row[d], str)


def test_rows_are_full_cross_product(rows):
    dims, unique_values = _group_by_dims(rows)
    expected = math.prod(len(v) for v in unique_values.values())
    assert len(rows) == expected


def test_stratum_columns_are_sequential(rows):
    dims = [k for k in rows[0] if k != "slope"]
    for i, d in enumerate(dims):
        assert d == f"stratum_{i + 1}"
