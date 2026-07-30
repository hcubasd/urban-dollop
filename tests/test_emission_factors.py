import pytest

from urban_dollop.synth.emission_factors import emission_factors


@pytest.fixture(scope="module")
def rows():
    return emission_factors()


def test_returns_list_of_dicts(rows):
    assert isinstance(rows, list)
    assert len(rows) >= 1


def test_has_required_columns(rows):
    for row in rows:
        for col in ("vehicle_type", "pollutant", "ef"):
            assert col in row


def test_pollutants_are_synthetic_labels(rows):
    for row in rows:
        assert row["pollutant"].startswith("pollutant_")


def test_ef_is_positive(rows):
    for row in rows:
        assert row["ef"] > 0.0


def test_full_cross_product(rows):
    vehicle_types = set(r["vehicle_type"] for r in rows)
    pollutants = set(r["pollutant"] for r in rows)
    assert len(rows) == len(vehicle_types) * len(pollutants)


def test_no_duplicate_rows(rows):
    keys = [(r["vehicle_type"], r["pollutant"]) for r in rows]
    assert len(keys) == len(set(keys))
