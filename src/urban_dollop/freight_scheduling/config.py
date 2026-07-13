from pathlib import Path

from pydantic import BaseModel


class FreightSchedulingConfig(BaseModel):
    """Configuration for the freight scheduler.

    No parameters are required — load consolidation is deterministic.
    The section exists for forward compatibility.
    """

    @classmethod
    def from_toml(cls, path: str | Path, section: str = "freight_scheduling") -> "FreightSchedulingConfig":
        import tomllib
        with open(path, "rb") as f:
            tomllib.load(f)  # validate TOML syntax; section may be absent
        return cls()
