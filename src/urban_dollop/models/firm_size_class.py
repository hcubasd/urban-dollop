from pathlib import Path
from typing import Self

from pydantic import BaseModel, model_validator

from urban_dollop.helpers.read_csv import read_csv


class FirmSizeClass(BaseModel):
    """One size-class bin of the firm size distribution for a given sector.

    Firm size is drawn uniformly from [lower_bound, upper_bound] when a firm
    falls into this class. The largest class per sector is conventionally
    open-ended; set upper_bound to a practical maximum (e.g. 1000).

    All classes for a given employment_sector must have probabilities summing
    to 1.0.
    """

    employment_sector: int
    firm_size_class: int
    lower_bound: float
    upper_bound: float
    probability: float

    @model_validator(mode="after")
    def check_bounds(self) -> "FirmSizeClass":
        if self.lower_bound <= 0:
            raise ValueError(
                f"lower_bound must be positive (got {self.lower_bound}); "
                "a firm with zero or fewer employees is not meaningful."
            )
        if self.upper_bound < self.lower_bound:
            raise ValueError(
                f"upper_bound ({self.upper_bound}) must be >= lower_bound ({self.lower_bound})."
            )
        return self

    @classmethod
    def from_file(cls, path: str | Path, columns: dict[str, str] = {}) -> list[Self]:
        path = Path(path)
        fields = list(cls.model_fields)
        required = [n for n, fi in cls.model_fields.items() if fi.is_required()]
        records = read_csv(path, columns, fields, required)
        return [cls(**r) for r in records]
