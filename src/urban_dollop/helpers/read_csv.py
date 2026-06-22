from pathlib import Path

import pandas as pd


def read_csv(
    path: str | Path,
    columns: dict[str, str],
    fields: list[str],
    required: list[str] | None = None,
) -> list[dict]:
    df = pd.read_csv(path)
    df = df.rename(columns={v: k for k, v in columns.items()})
    check = required if required is not None else fields
    missing = set(check) - set(df.columns)
    if missing:
        raise ValueError(
            f"Missing columns {missing} in {path}. "
            "Use columns= to map your column names to canonical names."
        )
    present = [f for f in fields if f in df.columns]
    return df[present].to_dict("records")
