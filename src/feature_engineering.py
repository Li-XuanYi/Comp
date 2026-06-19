"""Feature and panel construction helpers."""

from typing import Dict

import pandas as pd

from src.io_utils import get_project_root, load_paths, output_path, read_taxi_zone_lookup
from src.preprocessing import brooklyn_location_ids


def _processed_path(key: str, paths: Dict = None):
    paths = paths or load_paths()
    root = get_project_root(paths)
    destination = root / paths["node_outputs"][key]
    destination.parent.mkdir(parents=True, exist_ok=True)
    return destination


def build_hourly_demand_panel(paths: Dict = None) -> pd.DataFrame:
    """Build a complete zone-hour demand panel for January 2019."""
    paths = paths or load_paths()
    root = get_project_root(paths)
    interim_dir = root / paths["data"]["interim"]
    yellow = pd.read_parquet(interim_dir / "yellow_clean.parquet")
    green = pd.read_parquet(interim_dir / "green_clean.parquet")
    zone_ids = sorted(brooklyn_location_ids(paths))
    hours = pd.date_range("2019-01-01 00:00:00", "2019-01-31 23:00:00", freq="H")

    def aggregate(df: pd.DataFrame, count_name: str) -> pd.DataFrame:
        temp = df.copy()
        temp["zone_id"] = temp["PULocationID"].astype(int)
        temp["datetime_hour"] = pd.to_datetime(temp["pickup_datetime"]).dt.floor("H")
        return (
            temp.groupby(["zone_id", "datetime_hour"])
            .size()
            .rename(count_name)
            .reset_index()
        )

    yellow_counts = aggregate(yellow, "yellow_count")
    green_counts = aggregate(green, "green_count")
    base = pd.MultiIndex.from_product(
        [zone_ids, hours], names=["zone_id", "datetime_hour"]
    ).to_frame(index=False)
    panel = base.merge(yellow_counts, on=["zone_id", "datetime_hour"], how="left")
    panel = panel.merge(green_counts, on=["zone_id", "datetime_hour"], how="left")
    panel[["yellow_count", "green_count"]] = panel[
        ["yellow_count", "green_count"]
    ].fillna(0).astype(int)
    panel["pickup_count"] = panel["yellow_count"] + panel["green_count"]
    panel["date"] = panel["datetime_hour"].dt.date.astype(str)
    panel["hour"] = panel["datetime_hour"].dt.hour
    panel["weekday"] = panel["datetime_hour"].dt.weekday
    panel["is_weekend"] = panel["weekday"].isin([5, 6]).astype(int)

    lookup = read_taxi_zone_lookup(paths)[["LocationID", "Zone", "Borough"]]
    panel = panel.merge(
        lookup.rename(columns={"LocationID": "zone_id", "Zone": "zone_name"}),
        on="zone_id",
        how="left",
    )
    return panel[
        [
            "zone_id",
            "zone_name",
            "Borough",
            "datetime_hour",
            "date",
            "hour",
            "weekday",
            "is_weekend",
            "pickup_count",
            "yellow_count",
            "green_count",
        ]
    ]


def write_hourly_demand_panel(paths: Dict = None):
    paths = paths or load_paths()
    panel = build_hourly_demand_panel(paths)
    panel_path = _processed_path("node03_demand_panel", paths)
    panel.to_parquet(panel_path, index=False)

    summary = pd.DataFrame(
        [
            {
                "n_rows": len(panel),
                "n_zones": panel["zone_id"].nunique(),
                "datetime_min": panel["datetime_hour"].min(),
                "datetime_max": panel["datetime_hour"].max(),
                "total_pickups": int(panel["pickup_count"].sum()),
                "mean_hourly_pickups": float(panel["pickup_count"].mean()),
                "zero_demand_rows": int((panel["pickup_count"] == 0).sum()),
            }
        ]
    )
    summary_path = output_path("node03_demand_panel_summary", paths)
    summary.to_csv(summary_path, index=False, encoding="utf-8-sig")
    return panel_path

