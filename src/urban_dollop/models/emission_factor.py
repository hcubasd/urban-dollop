from pathlib import Path
from typing import Self

from pydantic import BaseModel

from urban_dollop.helpers.read_csv import read_csv


class EmissionFactor(BaseModel):
    """Speed-polynomial emission factor for one (vehicle, pollutant, gradient, load) cell.

    One row per combination. The polynomial EF formula is:
      EF [g/km] = (α·V² + β·V + γ + δ/V) / (ε·V² + ζ·V + η) · (1 − RF)
    where V is speed in km/h. This form is used by COPERT V, HBEFA, and
    compatible regional models; the coefficients in emission_factors.csv
    determine which model's calibration is applied.

    For non-exhaust PM (tyre/brake/road wear), set alpha=beta=delta=0,
    epsilon=zeta=0, eta=1 and encode the constant rate in gamma.
    """

    vehicle_id: int
    pollutant: str
    gradient_pct: float
    load_pct: float
    alpha: float
    beta: float
    gamma: float
    delta: float
    epsilon: float
    zeta: float
    eta: float
    rf: float

    @classmethod
    def from_file(cls, path: str | Path, columns: dict[str, str] = {}) -> list[Self]:
        records = read_csv(path, columns, list(cls.model_fields))
        return [cls(**r) for r in records]
