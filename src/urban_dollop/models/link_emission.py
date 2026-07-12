from pathlib import Path

import pandas as pd
from pydantic import BaseModel


class LinkEmission(BaseModel):
    link_id: int
    vehicle_id: int
    hour: int | None
    pollutant: str
    n_trips: int
    distance_m: float
    grade_pct: float
    emission_g: float

    @classmethod
    def to_file(cls, emissions: list["LinkEmission"], path: str | Path) -> None:
        pd.DataFrame([e.model_dump() for e in emissions]).to_csv(path, index=False)
