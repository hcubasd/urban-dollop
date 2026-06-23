from urban_dollop.models.zone import Zone


class LinearZone(Zone):
    """A zone with the socioeconomic attributes required by the linear demand formulation.

    Required by generate_parcel_demand. Households and employment are available
    from census data in any study area.
    """

    households: float
    employment: float
