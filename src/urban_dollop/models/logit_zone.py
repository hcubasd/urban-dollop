from urban_dollop.models.zone import Zone


class LogitZone(Zone):
    """A zone with the socioeconomic attributes required by the ordered logit demand formulation.

    Required by generate_logit_demand. Population and an integer urbanization
    classification are widely available from national statistics offices.
    """

    population: float
    urbanization_level: int
