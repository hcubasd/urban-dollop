from pathlib import Path

import pandas as pd


def write_csv(records: list[dict], path: str | Path) -> None:
    pd.DataFrame(records).to_csv(path, index=False)
