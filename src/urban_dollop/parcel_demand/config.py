from pydantic import BaseModel, field_validator


class ParcelDemandConfig(BaseModel):
    """Calibration parameters for parcel demand generation.

    Demand is derived from zone socioeconomics:
      - B2C: households × parcels_per_household / delivery_success_b2c
      - B2B: employment  × parcels_per_employee  / delivery_success_b2b

    The success rates correct for failed first-attempt deliveries so that
    the generated volume reflects shipments sent, not deliveries completed.
    """

    parcels_per_household: float
    parcels_per_employee: float
    delivery_success_b2c: float
    delivery_success_b2b: float
    default_vehicle_type: int
    random_seed: int | None = None

    @field_validator("parcels_per_household", "parcels_per_employee")
    @classmethod
    def must_be_non_negative(cls, v: float) -> float:
        if v < 0:
            raise ValueError(f"must be non-negative, got {v}")
        return v

    @field_validator("delivery_success_b2c", "delivery_success_b2b")
    @classmethod
    def must_be_in_unit_interval(cls, v: float) -> float:
        if not 0.0 < v <= 1.0:
            raise ValueError(f"must be in (0, 1], got {v}")
        return v
