"""Input/output helpers for raw data access and node-level artifacts."""

import json
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import pandas as pd
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PATHS_CONFIG = PROJECT_ROOT / "configs" / "paths.yaml"


def load_paths(config_path: Optional[Path] = None) -> Dict:
    """Load path configuration from YAML."""
    config_file = Path(config_path) if config_path else DEFAULT_PATHS_CONFIG
    with config_file.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def get_project_root(paths: Optional[Dict] = None) -> Path:
    """Return the configured project root as an absolute path."""
    paths = paths or load_paths()
    root_value = paths.get("project_root", ".")
    root = Path(root_value)
    if not root.is_absolute():
        root = PROJECT_ROOT / root
    return root.resolve()


def resolve_config_path(section: str, key: str, paths: Optional[Dict] = None) -> Path:
    """Resolve an exact path or glob pattern from `configs/paths.yaml`.

    Chinese source filenames may be displayed differently by some Windows
    consoles, so the config uses ASCII glob patterns. This function maps those
    stable patterns to concrete files inside the project root.
    """
    paths = paths or load_paths()
    root = get_project_root(paths)
    raw_value = paths[section][key]
    candidate = root / raw_value
    if candidate.exists():
        return candidate

    matches = sorted(root.glob(raw_value))
    if not matches:
        raise FileNotFoundError(
            "No path matched config {}.{}={!r}".format(section, key, raw_value)
        )
    if len(matches) > 1:
        exact_files = [match for match in matches if match.is_file()]
        matches = exact_files or matches
    return matches[0]


def output_path(key: str, paths: Optional[Dict] = None) -> Path:
    """Resolve a configured node output path and create its parent directory."""
    paths = paths or load_paths()
    root = get_project_root(paths)
    relative_path = paths["node_outputs"][key]
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def read_yellow_tripdata(paths: Optional[Dict] = None, **kwargs) -> pd.DataFrame:
    """Read the yellow taxi Excel attachment."""
    file_path = resolve_config_path("raw_inputs", "yellow_tripdata", paths)
    return pd.read_excel(file_path, **kwargs)


def read_green_tripdata(paths: Optional[Dict] = None, **kwargs) -> pd.DataFrame:
    """Read the green taxi Excel attachment."""
    file_path = resolve_config_path("raw_inputs", "green_tripdata", paths)
    return pd.read_excel(file_path, **kwargs)


def read_fhv_tripdata(paths: Optional[Dict] = None, **kwargs) -> pd.DataFrame:
    """Read the FHV Excel attachment."""
    file_path = resolve_config_path("raw_inputs", "fhv_tripdata", paths)
    return pd.read_excel(file_path, **kwargs)


def read_taxi_zone_lookup(paths: Optional[Dict] = None, **kwargs) -> pd.DataFrame:
    """Read the TLC taxi zone lookup CSV."""
    file_path = resolve_config_path("raw_inputs", "taxi_zone_lookup", paths)
    return pd.read_csv(file_path, **kwargs)


def read_taxi_zones_shp(paths: Optional[Dict] = None):
    """Read taxi zone shapefile attributes.

    If GeoPandas is installed, this returns a GeoDataFrame. Otherwise it falls
    back to pyshp and returns an attribute DataFrame, which is sufficient for
    Node 01 auditing.
    """
    file_path = resolve_config_path("raw_inputs", "taxi_zones_shp", paths)
    try:
        import geopandas as gpd  # type: ignore

        return gpd.read_file(file_path)
    except ImportError:
        import shapefile  # type: ignore

        reader = shapefile.Reader(str(file_path))
        fields = [field[0] for field in reader.fields if field[0] != "DeletionFlag"]
        records = [dict(zip(fields, record)) for record in reader.records()]
        return pd.DataFrame(records)


def _missing_rate_summary(df: pd.DataFrame) -> str:
    missing_rates = df.isna().mean().round(6).to_dict()
    return json.dumps(missing_rates, ensure_ascii=False, sort_keys=True)


def _datetime_bounds(df: pd.DataFrame) -> Dict[str, str]:
    datetime_columns = [
        column
        for column in df.columns
        if "date" in str(column).lower() or "time" in str(column).lower()
    ]
    values = []
    for column in datetime_columns:
        series = pd.to_datetime(df[column], errors="coerce")
        if series.notna().any():
            values.append(series)

    if not values:
        return {"datetime_min": "", "datetime_max": ""}

    combined = pd.concat(values, ignore_index=True).dropna()
    return {
        "datetime_min": combined.min().isoformat(sep=" "),
        "datetime_max": combined.max().isoformat(sep=" "),
    }


def audit_dataframe(dataset: str, df: pd.DataFrame) -> Dict[str, object]:
    """Build one audit record for a DataFrame-like input."""
    bounds = _datetime_bounds(df)
    return {
        "dataset": dataset,
        "n_rows": int(df.shape[0]),
        "n_cols": int(df.shape[1]),
        "columns": json.dumps([str(column) for column in df.columns], ensure_ascii=False),
        "missing_rate_summary": _missing_rate_summary(df),
        "datetime_min": bounds["datetime_min"],
        "datetime_max": bounds["datetime_max"],
    }


def build_data_audit(paths: Optional[Dict] = None) -> pd.DataFrame:
    """Read raw inputs and return the Node 01 audit table."""
    paths = paths or load_paths()
    readers = [
        ("yellow", read_yellow_tripdata),
        ("green", read_green_tripdata),
        ("fhv", read_fhv_tripdata),
        ("taxi_zone_lookup", read_taxi_zone_lookup),
        ("taxi_zones_shp", read_taxi_zones_shp),
    ]

    records: List[Dict[str, object]] = []
    for dataset, reader in readers:
        df = reader(paths)
        records.append(audit_dataframe(dataset, df))

    columns = [
        "dataset",
        "n_rows",
        "n_cols",
        "columns",
        "missing_rate_summary",
        "datetime_min",
        "datetime_max",
    ]
    return pd.DataFrame.from_records(records, columns=columns)


def write_data_audit(paths: Optional[Dict] = None) -> Path:
    """Generate and save `outputs/tables/node01_data_audit.csv`."""
    paths = paths or load_paths()
    audit = build_data_audit(paths)
    destination = output_path("node01_data_audit", paths)
    audit.to_csv(destination, index=False, encoding="utf-8-sig")
    return destination

