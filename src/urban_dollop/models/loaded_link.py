from pathlib import Path

import pandas as pd
from pydantic import BaseModel


class LoadedLink(BaseModel):
    link_id: int
    road_type: str
    distance_m: float
    grade_pct: float
    vehicle_id: int
    n_trips: int

    @classmethod
    def to_file(cls, links: list["LoadedLink"], path: str | Path) -> None:
        pd.DataFrame([l.model_dump() for l in links]).to_csv(path, index=False)
