from pathlib import Path

from pydantic import BaseModel


class FreightDemandConfig(BaseModel):
    """Configuration for the freight demand synthesizer.

    seed:
        RNG seed for reproducibility.  Omit or set to None for a random seed.
    sourcing_cost_per_hour:
        Monetary cost per hour used only in the distance-decay function when
        drawing sender zones.  Represents the cost of supply-chain sourcing
        time and is distinct from the vehicle-specific costs in
        freight_vehicle_params.csv.
    sourcing_cost_per_km:
        Monetary cost per km used only in the distance-decay function.
    distance_decay_alpha:
        Intercept (α) of the logistic distance-decay function
        f(c) = 1 / (1 + exp(α + β·ln c)).
    distance_decay_beta:
        Slope (β) of the logistic distance-decay function.
    """

    seed: int | None = None
    sourcing_cost_per_hour: float = 35.0
    sourcing_cost_per_km: float = 0.50
    distance_decay_alpha: float = -6.172
    distance_decay_beta: float = 2.180

    @classmethod
    def from_toml(cls, path: str | Path, section: str = "freight_demand") -> "FreightDemandConfig":
        import tomllib
        with open(path, "rb") as f:
            data = tomllib.load(f).get(section, {})
        return cls(**data)
