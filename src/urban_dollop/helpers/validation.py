from urban_dollop.models.depot import Depot
from urban_dollop.models.skim_matrix import SkimMatrix


def validate_depot_zones(depots: list[Depot], skim: SkimMatrix) -> None:
    missing = [d for d in depots if d.zone_id not in skim._pos]
    if missing:
        ids = ", ".join(str(d.depot_id) for d in missing)
        zones = ", ".join(str(d.zone_id) for d in missing)
        raise ValueError(
            f"Depot(s) {ids} have zone_id(s) {zones} not present in the skim matrix. "
            "Add these zones to your zones file or remove the depots."
        )


def validate_origin_zones(demands: list, skim: SkimMatrix) -> None:
    missing = sorted({d.origin_zone_id for d in demands if d.origin_zone_id not in skim._pos})
    if missing:
        zones = ", ".join(str(z) for z in missing)
        raise ValueError(
            f"Origin zone(s) {zones} not present in the skim matrix. "
            "Check your parcel demand file or skim matrix."
        )
