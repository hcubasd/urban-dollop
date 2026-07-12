from pathlib import Path
from typing import Self

import pandas as pd

from urban_dollop.models.zone import Zone


class LogitZone(Zone):
    """A zone with the socioeconomic attributes required by the ordered logit demand formulation.

    Required by generate_logit_demand. Population and an integer urbanization
    classification are widely available from national statistics offices.

    population_strata enables the full MASS-GT demographic stratification:
    a nested mapping of age_cohort_id → income_bracket_id → population count.
    When provided alongside beta_age and beta_income in LogitDemandConfig, the
    model computes expected parcels per demographic cell and sums across strata.
    When absent, the model uses total population and urbanization level only.
    """

    population: float
    urbanization_level: int
    population_strata: dict[int, dict[int, float]] | None = None

    @classmethod
    def from_file(
        cls,
        path: str | Path,
        columns: dict[str, str] = {},
        strata_path: str | Path | None = None,
    ) -> list[Self]:
        zones = super().from_file(path, columns)
        if strata_path is None:
            return zones
        strata = _load_strata(Path(strata_path))
        return [
            z.model_copy(update={"population_strata": strata.get(z.zone_id)})
            for z in zones
        ]


def _load_strata(path: Path) -> dict[int, dict[int, dict[int, float]]]:
    df = pd.read_csv(path)
    required = {"zone_id", "age_cohort", "income_bracket", "population"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(
            f"Missing columns {missing} in {path}. "
            "population_strata.csv must have columns: "
            "zone_id, age_cohort, income_bracket, population."
        )
    result: dict[int, dict[int, dict[int, float]]] = {}
    for row in df.itertuples(index=False):
        (
            result
            .setdefault(int(row.zone_id), {})
            .setdefault(int(row.age_cohort), {})
        )[int(row.income_bracket)] = float(row.population)
    return result
