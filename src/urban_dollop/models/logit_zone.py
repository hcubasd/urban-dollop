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
