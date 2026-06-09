import gzip
from pathlib import Path

import numpy as np
from pydantic import BaseModel, ConfigDict, PrivateAttr

from urban_dollop.models.zone import Zone


class SkimMatrix(BaseModel):
    """A square zone-to-zone travel skim matrix.

    Backed by a flat float32 array of N² values where element
    ``data[i * N + j]`` is the value from the zone at position i to the
    zone at position j. Positions are 0-based indices of zones sorted
    ascending by zone_id — the same order as the binary .mtx file.

    Use ``get()`` to look up values by zone_id rather than touching the
    array directly.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    data: np.ndarray
    zones: list[Zone]
    _pos: dict[int, int] = PrivateAttr()

    def model_post_init(self, __context) -> None:
        self._pos = {z.zone_id: i for i, z in enumerate(self.zones)}

    @property
    def n_zones(self) -> int:
        return len(self.zones)

    def get(self, from_zone_id: int, to_zone_id: int) -> float:
        """Look up the skim value between two zones by their zone_id."""
        return float(
            self.data[self._pos[from_zone_id] * self.n_zones + self._pos[to_zone_id]]
        )

    def submatrix(self, zone_ids: list[int]) -> np.ndarray:
        """Extract a contiguous sub-matrix for a subset of zones.

        Returns a (k×k) float32 array where element [i, j] is the skim value
        from zone_ids[i] to zone_ids[j]. Use this for tight loops that would
        otherwise call get() millions of times.
        """
        positions = np.array([self._pos[z] for z in zone_ids], dtype=np.intp)
        full = self.data.reshape(self.n_zones, self.n_zones)
        return full[np.ix_(positions, positions)]

    @classmethod
    def from_file(
        cls,
        path: str | Path,
        zones: list[Zone],
        headers: bool = False,
    ) -> "SkimMatrix":
        """Load a binary .mtx skim file.

        Parameters
        ----------
        path:
            Path to a binary .mtx file: flat float32 values, N² elements.
        zones:
            All zones in the scenario, including those with zero demand (depot
            locations, external zones). Used to validate matrix shape and to
            build the zone_id → position index. Sorted ascending by zone_id,
            matching the row/column order in the file.
        headers:
            Set to ``True`` if the file begins with a single value header
            containing the zone count (original MASS-GT format). The header
            is stripped before reading the matrix values. Default is
            ``False`` (headerless, urban-dollop canonical format).
        """
        zones = sorted(zones, key=lambda z: z.zone_id)
        path = Path(path)
        if path.suffix == ".gz":
            with gzip.open(path, "rb") as f:
                data = np.frombuffer(f.read(), dtype=np.float32).copy()
        else:
            data = np.fromfile(path, dtype=np.float32)
        if headers:
            data = data[1:]
        n = len(zones)
        if len(data) != n * n:
            raise ValueError(
                f"Expected {n}² = {n * n} values for {n} zones, got {len(data)}. "
                f"{'Try headers=True if the file includes a zone-count header.' if not headers else 'Ensure the file is correct.'}"
            )
        return cls(data=data, zones=zones)
