from pydantic import BaseModel, field_validator


class FirmSynthesisConfig(BaseModel):
    min_employment: float
    seed: int | None = None

    @field_validator("min_employment")
    @classmethod
    def min_employment_must_be_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("min_employment must be positive")
        return v
