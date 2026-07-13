import pytest

from urban_dollop.emission import EmissionCalculationConfig, calculate_emissions
from urban_dollop.models.emission_factor import EmissionFactor
from urban_dollop.models.loaded_link import LoadedLink
from urban_dollop.models.network_link import NetworkLink


def cfg(fill_rate=0.0, speed_urban=50.0):
    return EmissionCalculationConfig(
        speed_kmh={"urban": speed_urban},
        fill_rate=fill_rate,
    )


def nl(link_id=1, distance_m=1000.0, road_type="urban", grade_pct=0.0):
    return NetworkLink(
        link_id=link_id, from_node_id=link_id, to_node_id=link_id + 1,
        distance_m=distance_m, road_type=road_type, grade_pct=grade_pct,
    )


# ── basic output shape ───────────────────────────────────────────────────────


def test_one_link_one_pollutant(emission_factors, loaded_links_simple, network_links_simple):
    result = calculate_emissions(loaded_links_simple, emission_factors, network_links_simple, cfg())
    assert len(result) == 1
    r = result[0]
    assert r.link_id == 1
    assert r.vehicle_id == 1
    assert r.pollutant == "CO2"


def test_output_fields_populated(emission_factors, loaded_links_simple, network_links_simple):
    result = calculate_emissions(loaded_links_simple, emission_factors, network_links_simple, cfg())
    r = result[0]
    assert r.link_id == 1
    assert r.vehicle_id == 1
    assert r.pollutant == "CO2"
    assert r.hour is None
    assert r.emission_g == pytest.approx(100.0)


def test_empty_links_returns_empty(emission_factors):
    assert calculate_emissions([], emission_factors, [], cfg()) == []


def test_empty_factors_returns_empty(loaded_links_simple, network_links_simple):
    assert calculate_emissions(loaded_links_simple, [], network_links_simple, cfg()) == []


# ── emission quantity ────────────────────────────────────────────────────────


def test_emission_at_zero_grade_zero_load(emission_factors, loaded_links_simple, network_links_simple):
    # grade=0, fill_rate=0 → load=0 → EF=100 g/km; 1 trip × 1 km = 100 g
    result = calculate_emissions(loaded_links_simple, emission_factors, network_links_simple, cfg(fill_rate=0.0))
    assert result[0].emission_g == pytest.approx(100.0)


def test_emission_at_full_load(emission_factors, loaded_links_simple, network_links_simple):
    # grade=0, fill_rate=1 → load=100 → EF=200 g/km; 1 km = 200 g
    result = calculate_emissions(loaded_links_simple, emission_factors, network_links_simple, cfg(fill_rate=1.0))
    assert result[0].emission_g == pytest.approx(200.0)


def test_emission_at_half_load_interpolated(emission_factors, loaded_links_simple, network_links_simple):
    # grade=0, fill_rate=0.5 → load=50 → EF interpolated between 100 and 200 = 150
    result = calculate_emissions(loaded_links_simple, emission_factors, network_links_simple, cfg(fill_rate=0.5))
    assert result[0].emission_g == pytest.approx(150.0)


def test_emission_grade_interpolation(emission_factors):
    # grade=1, load=0 → EF interpolated between grad=0 (100) and grad=2 (150) = 125
    link = LoadedLink(link_id=1, vehicle_id=1, n_trips=1)
    result = calculate_emissions([link], emission_factors, [nl(grade_pct=1.0)], cfg(fill_rate=0.0))
    assert result[0].emission_g == pytest.approx(125.0)


def test_emission_bilinear_interpolation(emission_factors):
    # grade=1, fill_rate=0.5 (load=50)
    # EF at grad=0, load=50 = interp(100,200,0.5) = 150
    # EF at grad=2, load=50 = interp(150,300,0.5) = 225
    # EF at grad=1 = interp(150, 225, 0.5) = 187.5
    link = LoadedLink(link_id=1, vehicle_id=1, n_trips=1)
    result = calculate_emissions([link], emission_factors, [nl(grade_pct=1.0)], cfg(fill_rate=0.5))
    assert result[0].emission_g == pytest.approx(187.5)


def test_n_trips_scales_emission(emission_factors):
    link = LoadedLink(link_id=1, vehicle_id=1, n_trips=5)
    result = calculate_emissions([link], emission_factors, [nl()], cfg(fill_rate=0.0))
    assert result[0].emission_g == pytest.approx(500.0)


def test_distance_scales_emission(emission_factors):
    link = LoadedLink(link_id=1, vehicle_id=1, n_trips=1)
    result = calculate_emissions([link], emission_factors, [nl(distance_m=2000.0)], cfg(fill_rate=0.0))
    assert result[0].emission_g == pytest.approx(200.0)


# ── grade clamping ───────────────────────────────────────────────────────────


def test_grade_above_max_is_clamped(emission_factors):
    # grade=10 > max bin (2) → clamp to 2 → EF at grad=2, load=0 = 150
    link = LoadedLink(link_id=1, vehicle_id=1, n_trips=1)
    result = calculate_emissions([link], emission_factors, [nl(grade_pct=10.0)], cfg(fill_rate=0.0))
    assert result[0].emission_g == pytest.approx(150.0)


def test_grade_below_min_is_clamped(emission_factors):
    # grade=-5 < min bin (0) → clamp to 0 → EF = 100
    link = LoadedLink(link_id=1, vehicle_id=1, n_trips=1)
    result = calculate_emissions([link], emission_factors, [nl(grade_pct=-5.0)], cfg(fill_rate=0.0))
    assert result[0].emission_g == pytest.approx(100.0)


# ── multiple links / pollutants ──────────────────────────────────────────────


def test_multiple_links_produce_one_row_each(emission_factors):
    links = [
        LoadedLink(link_id=1, vehicle_id=1, n_trips=2),
        LoadedLink(link_id=2, vehicle_id=1, n_trips=1),
    ]
    nls = [
        NetworkLink(link_id=1, from_node_id=1, to_node_id=2, distance_m=1000.0, road_type="urban"),
        NetworkLink(link_id=2, from_node_id=2, to_node_id=3, distance_m=500.0, road_type="urban"),
    ]
    result = calculate_emissions(links, emission_factors, nls, cfg())
    assert len(result) == 2
    assert {r.link_id for r in result} == {1, 2}


def test_multiple_pollutants(loaded_links_simple, network_links_simple):
    nox_factors = [
        EmissionFactor(
            vehicle_id=1, pollutant="NOx",
            gradient_pct=0.0, load_pct=0.0,
            alpha=0, beta=0, gamma=50, delta=0,
            epsilon=0, zeta=0, eta=1, rf=0,
        ),
        EmissionFactor(
            vehicle_id=1, pollutant="NOx",
            gradient_pct=0.0, load_pct=100.0,
            alpha=0, beta=0, gamma=80, delta=0,
            epsilon=0, zeta=0, eta=1, rf=0,
        ),
        EmissionFactor(
            vehicle_id=1, pollutant="NOx",
            gradient_pct=2.0, load_pct=0.0,
            alpha=0, beta=0, gamma=60, delta=0,
            epsilon=0, zeta=0, eta=1, rf=0,
        ),
        EmissionFactor(
            vehicle_id=1, pollutant="NOx",
            gradient_pct=2.0, load_pct=100.0,
            alpha=0, beta=0, gamma=90, delta=0,
            epsilon=0, zeta=0, eta=1, rf=0,
        ),
    ]
    from tests.conftest import _make_ef
    co2_factors = [
        _make_ef(1, "CO2", 0.0, 0.0, 100.0),
        _make_ef(1, "CO2", 0.0, 100.0, 200.0),
        _make_ef(1, "CO2", 2.0, 0.0, 150.0),
        _make_ef(1, "CO2", 2.0, 100.0, 300.0),
    ]
    result = calculate_emissions(
        loaded_links_simple, co2_factors + nox_factors, network_links_simple, cfg()
    )
    assert len(result) == 2
    assert {r.pollutant for r in result} == {"CO2", "NOx"}


def test_hour_passed_through(emission_factors):
    link = LoadedLink(link_id=1, vehicle_id=1, n_trips=3, hour=8)
    result = calculate_emissions([link], emission_factors, [nl()], cfg())
    assert result[0].hour == 8


# ── COPERT V polynomial ──────────────────────────────────────────────────────


def test_rf_reduces_emission():
    factors = [
        EmissionFactor(
            vehicle_id=1, pollutant="CO2",
            gradient_pct=0.0, load_pct=0.0,
            alpha=0, beta=0, gamma=100, delta=0,
            epsilon=0, zeta=0, eta=1, rf=0.1,
        ),
        EmissionFactor(
            vehicle_id=1, pollutant="CO2",
            gradient_pct=0.0, load_pct=100.0,
            alpha=0, beta=0, gamma=100, delta=0,
            epsilon=0, zeta=0, eta=1, rf=0.1,
        ),
        EmissionFactor(
            vehicle_id=1, pollutant="CO2",
            gradient_pct=2.0, load_pct=0.0,
            alpha=0, beta=0, gamma=100, delta=0,
            epsilon=0, zeta=0, eta=1, rf=0.1,
        ),
        EmissionFactor(
            vehicle_id=1, pollutant="CO2",
            gradient_pct=2.0, load_pct=100.0,
            alpha=0, beta=0, gamma=100, delta=0,
            epsilon=0, zeta=0, eta=1, rf=0.1,
        ),
    ]
    link = LoadedLink(link_id=1, vehicle_id=1, n_trips=1)
    result = calculate_emissions([link], factors, [nl()], cfg(fill_rate=0.0))
    assert result[0].emission_g == pytest.approx(90.0)


def test_speed_affects_polynomial_emission():
    # alpha=1, all others=0, eta=1, rf=0 → EF = V² g/km
    factors = [
        EmissionFactor(
            vehicle_id=1, pollutant="PM",
            gradient_pct=0.0, load_pct=0.0,
            alpha=1, beta=0, gamma=0, delta=0,
            epsilon=0, zeta=0, eta=1, rf=0,
        ),
        EmissionFactor(
            vehicle_id=1, pollutant="PM",
            gradient_pct=0.0, load_pct=100.0,
            alpha=1, beta=0, gamma=0, delta=0,
            epsilon=0, zeta=0, eta=1, rf=0,
        ),
        EmissionFactor(
            vehicle_id=1, pollutant="PM",
            gradient_pct=2.0, load_pct=0.0,
            alpha=1, beta=0, gamma=0, delta=0,
            epsilon=0, zeta=0, eta=1, rf=0,
        ),
        EmissionFactor(
            vehicle_id=1, pollutant="PM",
            gradient_pct=2.0, load_pct=100.0,
            alpha=1, beta=0, gamma=0, delta=0,
            epsilon=0, zeta=0, eta=1, rf=0,
        ),
    ]
    link = LoadedLink(link_id=1, vehicle_id=1, n_trips=1)
    # Speed = 10 km/h → EF = 10² = 100 g/km; 1 km → 100 g
    result = calculate_emissions([link], factors, [nl()], cfg(speed_urban=10.0))
    assert result[0].emission_g == pytest.approx(100.0)

    # Speed = 20 km/h → EF = 400 g/km; 1 km → 400 g
    result2 = calculate_emissions([link], factors, [nl()], cfg(speed_urban=20.0))
    assert result2[0].emission_g == pytest.approx(400.0)


# ── validation errors ────────────────────────────────────────────────────────


def test_missing_vehicle_factors_raises(loaded_links_simple, network_links_simple):
    factors = [
        EmissionFactor(
            vehicle_id=99, pollutant="CO2",
            gradient_pct=0.0, load_pct=0.0,
            alpha=0, beta=0, gamma=100, delta=0,
            epsilon=0, zeta=0, eta=1, rf=0,
        ),
    ]
    with pytest.raises(ValueError, match="Vehicle IDs"):
        calculate_emissions(loaded_links_simple, factors, network_links_simple, cfg())


def test_missing_road_type_speed_raises(emission_factors):
    link = LoadedLink(link_id=1, vehicle_id=1, n_trips=1)
    with pytest.raises(ValueError, match="speed"):
        calculate_emissions([link], emission_factors, [nl(road_type="highway")], cfg())


def test_missing_link_in_network_links_raises(emission_factors):
    link = LoadedLink(link_id=99, vehicle_id=1, n_trips=1)
    with pytest.raises(ValueError, match="Link IDs"):
        calculate_emissions([link], emission_factors, [nl(link_id=1)], cfg())


def test_incomplete_factor_grid_raises():
    # CO2 has a 2×2 grid (grad 0/2, load 0/100)
    # NOx has only 1 cell — missing the other three from the global grid
    from tests.conftest import _make_ef
    factors = [
        _make_ef(1, "CO2", 0.0, 0.0, 100.0),
        _make_ef(1, "CO2", 0.0, 100.0, 200.0),
        _make_ef(1, "CO2", 2.0, 0.0, 150.0),
        _make_ef(1, "CO2", 2.0, 100.0, 300.0),
        # NOx missing (0, 100), (2, 0), (2, 100):
        _make_ef(1, "NOx", 0.0, 0.0, 50.0),
    ]
    link = LoadedLink(link_id=1, vehicle_id=1, n_trips=1)
    with pytest.raises(ValueError, match="Incomplete emission factor grid"):
        calculate_emissions([link], factors, [nl()], cfg())


def test_config_required_raises(emission_factors, loaded_links_simple, network_links_simple):
    with pytest.raises(ValueError, match="EmissionCalculationConfig"):
        calculate_emissions(loaded_links_simple, emission_factors, network_links_simple, config=None)
