from pydantic import BaseModel, field_validator


class ParcelSchedulingConfig(BaseModel):
    """Calibration parameters for parcel delivery scheduling."""

    seed: int | None = None
    departure_time_distribution: list[float] | None = None

    @field_validator("departure_time_distribution")
    @classmethod
    def validate_departure_distribution(cls, v: list[float] | None) -> list[float] | None:
        if v is None:
            return v
        if len(v) != 24:
            raise ValueError(
                f"departure_time_distribution must have exactly 24 values (one per hour), got {len(v)}"
            )
        if any(x < 0.0 or x > 1.0 for x in v):
            raise ValueError("departure_time_distribution values must be in [0, 1]")
        for i in range(1, 24):
            if v[i] < v[i - 1]:
                raise ValueError("departure_time_distribution must be non-decreasing (cumulative shares)")
        if abs(v[-1] - 1.0) > 1e-6:
            raise ValueError(
                f"departure_time_distribution is a CDF: the last value must be 1.0, got {v[-1]}"
            )
        return v
