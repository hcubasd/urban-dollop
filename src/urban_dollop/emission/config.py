from pydantic import BaseModel


class EmissionCalculationConfig(BaseModel):
    speed_kmh: dict[str, float]
    fill_rate: float
