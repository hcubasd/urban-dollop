from collections import defaultdict
from typing import Any

import numpy as np
from shapely.geometry import Point

from urban_dollop.firm_synthesis.config import FirmSynthesisConfig
from urban_dollop.models.firm import Firm
from urban_dollop.models.firm_size_class import FirmSizeClass
from urban_dollop.models.zone import Zone
from urban_dollop.models.zone_employment import ZoneEmployment

_MAX_PLACEMENT_TRIES = 500


def synthesize_firms(
    zones: list[Zone],
    zone_employment: list[ZoneEmployment],
    firm_size_classes: list[FirmSizeClass],
    config: FirmSynthesisConfig,
    zone_polygons: dict[int, Any] | None = None,
) -> list[Firm]:
    """Synthesise a firm register from zone employment and a size distribution.

    For each (zone, sector) employment cell, draws firms sequentially from
    the size class distribution until the cell's employment is exhausted.
    Firms whose employment falls below config.min_employment are discarded
    after synthesis. Surviving firms are renumbered sequentially from 1.

    Each firm is placed at a random coordinate within its zone polygon when
    zone_polygons is provided; otherwise it is placed at the zone centroid
    (x, y on the Zone object). Polygon rejection sampling falls back to the
    polygon centroid after _MAX_PLACEMENT_TRIES failed attempts.

    Args:
        zones: Zone objects supplying centroid coordinates (x, y).
        zone_employment: Employment by zone × sector. Each record drives one
            synthesis loop.
        firm_size_classes: Size class distribution by sector. All classes for
            a sector must have probabilities summing to 1.0.
        config: min_employment threshold and optional RNG seed.
        zone_polygons: Optional Shapely Polygon per zone_id. When provided,
            firms are placed at random points within the polygon rather than
            at the centroid.

    Returns:
        List of Firm records with sequential firm_id starting at 1.
    """
    rng = np.random.default_rng(config.seed)

    zone_coords: dict[int, tuple[float, float]] = {
        z.zone_id: (z.x, z.y)
        for z in zones
        if z.x is not None and z.y is not None
    }

    classes_by_sector: dict[int, list[FirmSizeClass]] = defaultdict(list)
    for fsc in firm_size_classes:
        classes_by_sector[fsc.employment_sector].append(fsc)
    for classes in classes_by_sector.values():
        classes.sort(key=lambda c: c.firm_size_class)

    _validate_sector_coverage(zone_employment, classes_by_sector)
    _validate_probabilities(classes_by_sector)

    cumulative_by_sector: dict[int, np.ndarray] = {
        sector: np.cumsum([c.probability for c in classes])
        for sector, classes in classes_by_sector.items()
    }

    raw: list[tuple[int, int, float, float, float]] = []

    for ze in zone_employment:
        remaining = ze.employment
        classes = classes_by_sector[ze.employment_sector]
        cumulative = cumulative_by_sector[ze.employment_sector]

        while remaining > 0:
            u = rng.random()
            class_idx = min(int(np.searchsorted(cumulative, u)), len(classes) - 1)
            sc = classes[class_idx]

            employment = float(rng.uniform(sc.lower_bound, sc.upper_bound))
            employment = min(employment, remaining)
            remaining -= employment

            x, y = _sample_location(ze.zone_id, zone_coords, zone_polygons, rng)
            raw.append((ze.zone_id, ze.employment_sector, employment, x, y))

    kept = [(z, s, e, x, y) for z, s, e, x, y in raw if e >= config.min_employment]
    return [
        Firm(
            firm_id=i,
            zone_id=z,
            employment_sector=s,
            employment=e,
            x_coord=x,
            y_coord=y,
        )
        for i, (z, s, e, x, y) in enumerate(kept, start=1)
    ]


def _sample_location(
    zone_id: int,
    zone_coords: dict[int, tuple[float, float]],
    zone_polygons: dict[int, Any] | None,
    rng: np.random.Generator,
) -> tuple[float, float]:
    if zone_polygons is not None and zone_id in zone_polygons:
        return _sample_in_polygon(zone_polygons[zone_id], rng)
    if zone_id in zone_coords:
        return zone_coords[zone_id]
    raise ValueError(
        f"Zone {zone_id} has no centroid coordinates and no polygon. "
        "Load zones from a GeoPackage or provide x and y columns in zones.csv."
    )


def _sample_in_polygon(polygon: Any, rng: np.random.Generator) -> tuple[float, float]:
    minx, miny, maxx, maxy = polygon.bounds
    for _ in range(_MAX_PLACEMENT_TRIES):
        x = float(rng.uniform(minx, maxx))
        y = float(rng.uniform(miny, maxy))
        if polygon.contains(Point(x, y)):
            return x, y
    centroid = polygon.centroid
    return float(centroid.x), float(centroid.y)


def _validate_sector_coverage(
    zone_employment: list[ZoneEmployment],
    classes_by_sector: dict[int, list[FirmSizeClass]],
) -> None:
    missing = {ze.employment_sector for ze in zone_employment} - set(classes_by_sector)
    if missing:
        raise ValueError(
            f"Employment sectors {sorted(missing)} appear in zone_employment but have "
            "no size class entries. Add rows to firm_size_distribution.csv for each sector."
        )


def _validate_probabilities(
    classes_by_sector: dict[int, list[FirmSizeClass]],
    tolerance: float = 1e-3,
) -> None:
    bad = [
        sector
        for sector, classes in classes_by_sector.items()
        if abs(sum(c.probability for c in classes) - 1.0) > tolerance
    ]
    if bad:
        raise ValueError(
            f"Firm size class probabilities do not sum to 1.0 for sectors: {sorted(bad)}. "
            "Check firm_size_distribution.csv."
        )
