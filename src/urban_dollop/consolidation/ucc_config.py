from pydantic import BaseModel, field_validator


class UCCConfig(BaseModel):
    """Configuration for the UCC consolidation module.

    probability controls the fraction of eligible parcels (those destined
    for a UCC catchment zone) that are rerouted through an Urban
    Consolidation Centre. Applied deterministically to aggregated parcel
    counts: rerouted = round(n_parcels * probability).
    """

    probability: float

    @field_validator("probability")
    @classmethod
    def probability_in_range(cls, v: float) -> float:
        if not 0 < v <= 1.0:
            raise ValueError(f"probability must be in (0, 1], got {v}")
        return v
