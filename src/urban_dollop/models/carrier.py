from pydantic import field_validator

from urban_dollop.models.base import FileModel


class Carrier(FileModel):
    """A parcel delivery carrier with a market share fraction.

    Market shares must sum to 1 across all carriers in a scenario.
    The share drives how total zonal demand is split between carriers
    before depot assignment.
    """

    carrier: str
    share: float

    @field_validator("share")
    @classmethod
    def share_in_unit_interval(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError(f"share must be in [0, 1], got {v}")
        return v
