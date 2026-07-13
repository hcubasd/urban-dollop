import csv
from pathlib import Path
from typing import Self

from pydantic import BaseModel


class FreightMNLParam(BaseModel):
    """One MNL parameter for the joint shipment-size × vehicle-type model.

    logistic_segment: the LS this parameter applies to, or -1 for a global
    default that is used when no LS-specific value is provided.

    Recognised parameter names:
      B_TransportCosts   — disutility coefficient for transport cost
      B_InventoryCosts   — disutility coefficient for shipment weight (inventory)
      ASC_VT_{vehicle_id} — alternative-specific constant for vehicle type
      ASC_SS_{size_class} — alternative-specific constant for size class

    In the CSV, logistic_segment may be written as ``*`` to mean global
    default; the loader converts it to -1.
    """

    logistic_segment: int
    parameter: str
    value: float

    @classmethod
    def from_file(cls, path: str | Path) -> list[Self]:
        records: list[Self] = []
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                raw_ls = row["logistic_segment"].strip()
                ls = -1 if raw_ls == "*" else int(raw_ls)
                records.append(cls(logistic_segment=ls, parameter=row["parameter"].strip(), value=float(row["value"])))
        return records
