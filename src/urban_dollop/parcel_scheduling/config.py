from pydantic import BaseModel


class ParcelSchedulingConfig(BaseModel):
    """Calibration parameters for parcel delivery scheduling."""

    seed: int | None = None
