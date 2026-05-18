from pathlib import Path

import geopandas as gpd


def read_gpkg(path: str | Path, columns: dict[str, str], fields: list[str]) -> list[dict]:
    df = gpd.read_file(path)
    df = df.rename(columns={v: k for k, v in columns.items()})
    missing = set(fields) - set(df.columns)
    if missing:
        raise ValueError(
            f"Missing columns {missing} in {path}. "
            "Use columns= to map your column names to canonical names."
        )
    return df[fields].to_dict("records")
