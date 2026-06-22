from urban_dollop.models.skim_matrix import SkimMatrix


class SkimDistance(SkimMatrix):
    """A square zone-to-zone travel distance skim matrix.

    Identical structure to SkimMatrix but holds distances (metres or
    kilometres depending on the source data) rather than travel times.
    Used by the consolidation modules to find the nearest microhub or
    UCC by minimising total leg distance.
    """
