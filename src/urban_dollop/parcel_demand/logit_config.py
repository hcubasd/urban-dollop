from pydantic import BaseModel, field_validator, model_validator


class LogitDemandConfig(BaseModel):
    """Calibration parameters for the HARMONY v3 ordered logit parcel demand model.

    The logit model computes expected monthly B2C parcels per person using an
    ordered logit over urbanization level, then converts to daily demand and
    multiplies by zone population.

    beta_urbanization maps each urbanization level integer to its linear predictor
    coefficient. Zones whose urbanization_level is not present in the mapping
    receive coefficient 0.

    mu_thresholds contains one threshold per parcel level except the last; the
    last level has cumulative probability 1 by convention. len(mu_thresholds)
    must equal len(parcel_levels) - 1.

    Parameters are estimated from survey data. Dutch estimates from HARMONY v3
    (de Bok et al. 2025) may be used as a prior when local data are not available.
    """

    beta_urbanization: dict[int, float]
    mu_thresholds: list[float]
    parcel_levels: list[int]
    monthly_to_daily_divisor: float
    calibration_target: float | None = None

    @model_validator(mode="after")
    def mu_length_matches_levels(self) -> "LogitDemandConfig":
        expected = len(self.parcel_levels) - 1
        if len(self.mu_thresholds) != expected:
            raise ValueError(
                f"mu_thresholds must have {expected} entries "
                f"(one per parcel level except the last), got {len(self.mu_thresholds)}"
            )
        return self

    @field_validator("monthly_to_daily_divisor")
    @classmethod
    def divisor_must_be_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError(f"must be positive, got {v}")
        return v

    @field_validator("calibration_target")
    @classmethod
    def calibration_must_be_positive(cls, v: float | None) -> float | None:
        if v is not None and v <= 0:
            raise ValueError(f"must be positive, got {v}")
        return v
