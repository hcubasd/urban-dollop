from pydantic import BaseModel, field_validator


class EmissionCalculationConfig(BaseModel):
    speed_kmh: dict[str, float]
    fill_rate: float

    @field_validator("speed_kmh")
    @classmethod
    def speeds_must_be_positive(cls, v: dict[str, float]) -> dict[str, float]:
        zero_or_negative = [rt for rt, spd in v.items() if spd <= 0]
        if zero_or_negative:
            raise ValueError(
                f"speed_kmh must be positive; got zero or negative for road types: "
                f"{zero_or_negative}"
            )
        return v
