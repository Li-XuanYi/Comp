"""Node 02 preprocessing: schema normalization and anomaly filtering."""

from pathlib import Path
from typing import Dict, Iterable, Tuple

import pandas as pd

from src.io_utils import (
    get_project_root,
    load_paths,
    output_path,
    read_fhv_tripdata,
    read_green_tripdata,
    read_taxi_zone_lookup,
    read_yellow_tripdata,
)


JAN_START = pd.Timestamp("2019-01-01")
FEB_START = pd.Timestamp("2019-02-01")


def brooklyn_location_ids(paths: Dict = None) -> set:
    lookup = read_taxi_zone_lookup(paths)
    return set(
        lookup.loc[lookup["Borough"].astype(str).str.lower() == "brooklyn", "LocationID"]
        .dropna()
        .astype(int)
    )


def standardize_trip_columns(df: pd.DataFrame, dataset: str) -> pd.DataFrame:
    rename_map = {}
    if dataset == "yellow":
        rename_map = {
            "tpep_pickup_datetime": "pickup_datetime",
            "tpep_dropoff_datetime": "dropoff_datetime",
        }
    elif dataset == "green":
        rename_map = {
            "lpep_pickup_datetime": "pickup_datetime",
            "lpep_dropoff_datetime": "dropoff_datetime",
        }
    elif dataset == "fhv":
        rename_map = {
            "Pickup_datetime": "pickup_datetime",
            "DropOff_datetime": "dropoff_datetime",
            "dropoff_datetime": "dropoff_datetime",
        }
    out = df.rename(columns=rename_map).copy()
    out["pickup_datetime"] = pd.to_datetime(out["pickup_datetime"], errors="coerce")
    out["dropoff_datetime"] = pd.to_datetime(out["dropoff_datetime"], errors="coerce")
    out["duration_min"] = (
        out["dropoff_datetime"] - out["pickup_datetime"]
    ).dt.total_seconds() / 60.0
    return out


def clean_trip_data(
    df: pd.DataFrame, dataset: str, brooklyn_ids: Iterable[int]
) -> Tuple[pd.DataFrame, Dict[str, int]]:
    """Clean one raw trip table according to Node 02 rules."""
    out = standardize_trip_columns(df, dataset)
    original_rows = len(out)
    brooklyn_ids = set(int(value) for value in brooklyn_ids)

    mask = (
        out["pickup_datetime"].ge(JAN_START)
        & out["pickup_datetime"].lt(FEB_START)
        & out["dropoff_datetime"].gt(out["pickup_datetime"])
        & out["duration_min"].gt(0)
        & out["duration_min"].le(180)
        & out["PULocationID"].isin(brooklyn_ids)
    )

    if dataset in {"yellow", "green"}:
        mask = (
            mask
            & out["trip_distance"].gt(0)
            & out["total_amount"].gt(0)
            & out["fare_amount"].gt(0)
            & out["fare_amount"].le(500)
            & out["total_amount"].le(1000)
        )

    cleaned = out.loc[mask].copy()
    if dataset == "fhv":
        keep_columns = [
            "dispatching_base_num",
            "pickup_datetime",
            "dropoff_datetime",
            "PULocationID",
            "DOLocationID",
            "SR_Flag",
            "duration_min",
        ]
        cleaned = cleaned[keep_columns]

    report = {
        "dataset": dataset,
        "raw_rows": int(original_rows),
        "clean_rows": int(len(cleaned)),
        "removed_rows": int(original_rows - len(cleaned)),
    }
    return cleaned, report


def write_clean_outputs(paths: Dict = None) -> Path:
    """Generate Node 02 clean parquet files and cleaning report."""
    paths = paths or load_paths()
    root = get_project_root(paths)
    interim_dir = root / paths["data"]["interim"]
    interim_dir.mkdir(parents=True, exist_ok=True)

    brooklyn_ids = brooklyn_location_ids(paths)
    datasets = [
        ("yellow", read_yellow_tripdata(paths)),
        ("green", read_green_tripdata(paths)),
        ("fhv", read_fhv_tripdata(paths)),
    ]

    reports = []
    for dataset, raw in datasets:
        cleaned, report = clean_trip_data(raw, dataset, brooklyn_ids)
        cleaned.to_parquet(interim_dir / "{}_clean.parquet".format(dataset), index=False)
        reports.append(report)

    report_path = output_path("node02_cleaning_report", paths)
    pd.DataFrame(reports).to_csv(report_path, index=False, encoding="utf-8-sig")
    return report_path

