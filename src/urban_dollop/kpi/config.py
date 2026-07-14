from pathlib import Path

from pydantic import BaseModel


class KPIConfig(BaseModel):
    """Configuration for KPI calculation. Currently has no parameters."""

    @classmethod
    def from_toml(cls, path: str | Path, section: str = "kpi") -> "KPIConfig":
        import tomllib
        with open(path, "rb") as f:
            tomllib.load(f)
        return cls()
