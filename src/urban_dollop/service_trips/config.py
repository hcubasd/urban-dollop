from pathlib import Path

from pydantic import BaseModel


class ServiceTripConfig(BaseModel):
    """Configuration for the service trip generator.

    seed:
        RNG seed for reproducibility.  Controls both the stochastic rounding
        of fractional trip counts and the destination/vehicle draws.
    distance_decay_alpha:
        Intercept (α) of the logistic decay function
        f(t) = 1 / (1 + exp(α + β·ln t)) where t is travel time in minutes.
    distance_decay_beta:
        Slope (β) of the logistic decay function.  A larger positive value
        makes the decay steeper, concentrating trips in nearby zones.
    """

    seed: int | None = None
    distance_decay_alpha: float = -1.5
    distance_decay_beta: float = 2.0

    @classmethod
    def from_toml(cls, path: str | Path, section: str = "service_trips") -> "ServiceTripConfig":
        import tomllib
        with open(path, "rb") as f:
            data = tomllib.load(f).get(section, {})
        return cls(**data)
