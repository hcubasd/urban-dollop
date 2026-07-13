import pytest

from urban_dollop.firm_synthesis import FirmSynthesisConfig, synthesize_firms
from urban_dollop.models.firm_size_class import FirmSizeClass
from urban_dollop.models.zone import Zone
from urban_dollop.models.zone_employment import ZoneEmployment


def zone(zone_id=1, x=0.0, y=0.0):
    return Zone(zone_id=zone_id, x=x, y=y)


def ze(zone_id=1, sector=1, employment=20.0):
    return ZoneEmployment(zone_id=zone_id, employment_sector=sector, employment=employment)


def fsc(sector=1, cls=1, lower=2.0, upper=5.0, probability=1.0):
    return FirmSizeClass(
        employment_sector=sector,
        firm_size_class=cls,
        lower_bound=lower,
        upper_bound=upper,
        probability=probability,
    )


def cfg(min_employment=1.0, seed=0):
    return FirmSynthesisConfig(min_employment=min_employment, seed=seed)


# ── output shape ─────────────────────────────────────────────────────────────


def test_produces_at_least_one_firm():
    firms = synthesize_firms([zone()], [ze(employment=10.0)], [fsc()], cfg())
    assert len(firms) > 0


def test_firm_ids_sequential_from_one():
    firms = synthesize_firms([zone()], [ze(employment=30.0)], [fsc()], cfg())
    assert [f.firm_id for f in firms] == list(range(1, len(firms) + 1))


def test_zone_and_sector_carried_through():
    firms = synthesize_firms(
        [zone(zone_id=7)],
        [ze(zone_id=7, sector=3, employment=10.0)],
        [fsc(sector=3)],
        cfg(),
    )
    assert all(f.zone_id == 7 for f in firms)
    assert all(f.employment_sector == 3 for f in firms)


def test_employment_within_class_bounds():
    firms = synthesize_firms([zone()], [ze(employment=50.0)], [fsc(lower=2.0, upper=5.0)], cfg())
    # All firms except possibly the last (capped at remaining) should be in [2, 5]
    for f in firms[:-1]:
        assert 2.0 <= f.employment <= 5.0


def test_total_employment_approximately_allocated():
    total = 50.0
    firms = synthesize_firms([zone()], [ze(employment=total)], [fsc(lower=2.0, upper=5.0)], cfg())
    # Sum of firm employment should be ≤ total (last firm capped) and within one class width
    s = sum(f.employment for f in firms)
    assert s <= total
    assert s >= total - 5.0  # within one class upper_bound of total


# ── min_employment filter ─────────────────────────────────────────────────────


def test_firms_below_min_employment_filtered():
    # Class spans [1, 3]; min_employment = 5 → all firms discarded
    firms = synthesize_firms(
        [zone()],
        [ze(employment=20.0)],
        [fsc(lower=1.0, upper=3.0)],
        FirmSynthesisConfig(min_employment=5.0, seed=0),
    )
    assert firms == []


def test_firms_at_min_employment_kept():
    # Class is a single point at exactly min_employment
    firms = synthesize_firms(
        [zone()],
        [ze(employment=20.0)],
        [fsc(lower=3.0, upper=3.0)],
        FirmSynthesisConfig(min_employment=3.0, seed=0),
    )
    assert len(firms) > 0
    assert all(f.employment >= 3.0 for f in firms)


# ── multi-zone / multi-sector ─────────────────────────────────────────────────


def test_multiple_zones_produce_separate_firms():
    firms = synthesize_firms(
        [zone(zone_id=1, x=0.0, y=0.0), zone(zone_id=2, x=10.0, y=10.0)],
        [ze(zone_id=1, employment=10.0), ze(zone_id=2, employment=10.0)],
        [fsc()],
        cfg(),
    )
    assert any(f.zone_id == 1 for f in firms)
    assert any(f.zone_id == 2 for f in firms)


def test_multiple_sectors_produce_separate_firms():
    firms = synthesize_firms(
        [zone()],
        [ze(sector=1, employment=10.0), ze(sector=2, employment=10.0)],
        [fsc(sector=1), fsc(sector=2)],
        cfg(),
    )
    assert any(f.employment_sector == 1 for f in firms)
    assert any(f.employment_sector == 2 for f in firms)


# ── size class distribution ───────────────────────────────────────────────────


def test_two_classes_both_sampled_over_many_draws():
    firms = synthesize_firms(
        [zone()],
        [ze(employment=500.0)],
        [
            fsc(cls=1, lower=1.0, upper=2.0, probability=0.5),
            fsc(cls=2, lower=10.0, upper=20.0, probability=0.5),
        ],
        cfg(),
    )
    small = [f for f in firms if f.employment <= 2.0]
    large = [f for f in firms if f.employment >= 10.0]
    assert len(small) > 0
    assert len(large) > 0


# ── coordinates ──────────────────────────────────────────────────────────────


def test_firms_placed_at_zone_centroid_without_polygons():
    firms = synthesize_firms(
        [zone(x=3.5, y=7.2)],
        [ze(employment=10.0)],
        [fsc()],
        cfg(),
    )
    assert all(f.x_coord == pytest.approx(3.5) for f in firms)
    assert all(f.y_coord == pytest.approx(7.2) for f in firms)


def test_firms_placed_within_polygon_bounds():
    from shapely.geometry import box

    polygon = box(0.0, 0.0, 10.0, 10.0)
    firms = synthesize_firms(
        [zone(x=5.0, y=5.0)],
        [ze(employment=30.0)],
        [fsc()],
        cfg(),
        zone_polygons={1: polygon},
    )
    for f in firms:
        assert 0.0 <= f.x_coord <= 10.0
        assert 0.0 <= f.y_coord <= 10.0


# ── reproducibility ───────────────────────────────────────────────────────────


def test_seed_makes_synthesis_reproducible():
    args = ([zone()], [ze(employment=30.0)], [fsc()], cfg(seed=42))
    firms_a = synthesize_firms(*args)
    firms_b = synthesize_firms(*args)
    assert len(firms_a) == len(firms_b)
    assert firms_a[0].employment == pytest.approx(firms_b[0].employment)


# ── validation errors ─────────────────────────────────────────────────────────


def test_missing_sector_raises():
    with pytest.raises(ValueError, match="sectors"):
        synthesize_firms([zone()], [ze(sector=99)], [fsc(sector=1)], cfg())


def test_probabilities_not_summing_to_one_raises():
    with pytest.raises(ValueError, match="probabilities"):
        synthesize_firms(
            [zone()],
            [ze()],
            [fsc(cls=1, probability=0.6)],  # sums to 0.6, not 1.0
            cfg(),
        )


def test_zone_without_coordinates_raises():
    zone_no_coords = Zone(zone_id=1)  # x=None, y=None
    with pytest.raises(ValueError, match="centroid"):
        synthesize_firms([zone_no_coords], [ze()], [fsc()], cfg())


def test_min_employment_zero_raises():
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        FirmSynthesisConfig(min_employment=0.0, seed=0)
