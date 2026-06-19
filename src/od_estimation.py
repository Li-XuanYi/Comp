"""Node 08 OD distance and duration estimation."""

from itertools import product
from typing import Dict, Tuple

import numpy as np
import pandas as pd

from src.io_utils import get_project_root, load_paths, output_path, resolve_config_path
from src.preprocessing import brooklyn_location_ids


def load_zone_centroids(paths: Dict = None) -> pd.DataFrame:
    import shapefile  # type: ignore

    shp_path = resolve_config_path("raw_inputs", "taxi_zones_shp", paths)
    reader = shapefile.Reader(str(shp_path))
    fields = [field[0] for field in reader.fields if field[0] != "DeletionFlag"]
    records = []
    for shape, record in zip(reader.shapes(), reader.records()):
        attrs = dict(zip(fields, record))
        points = np.asarray(shape.points, dtype=float)
        centroid = points.mean(axis=0)
        records.append(
            {
                "LocationID": int(attrs["LocationID"]),
                "borough": attrs.get("borough"),
                "x": float(centroid[0]),
                "y": float(centroid[1]),
            }
        )
    return pd.DataFrame(records).drop_duplicates("LocationID")


def centroid_distance_miles(pu: int, do: int, centroids: pd.DataFrame) -> float:
    lookup = centroids.set_index("LocationID")
    if pu not in lookup.index or do not in lookup.index:
        return np.nan
    dx = lookup.loc[pu, "x"] - lookup.loc[do, "x"]
    dy = lookup.loc[pu, "y"] - lookup.loc[do, "y"]
    if pu == do:
        return 0.5
    return max(float(np.sqrt(dx * dx + dy * dy) / 5280.0), 0.5)


def historical_od_reference(yellow: pd.DataFrame, green: pd.DataFrame) -> pd.DataFrame:
    taxi = pd.concat([yellow, green], ignore_index=True)
    grouped = (
        taxi.groupby(["PULocationID", "DOLocationID"])
        .agg(
            n_samples=("trip_distance", "size"),
            historical_distance=("trip_distance", "median"),
            historical_duration=("duration_min", "median"),
        )
        .reset_index()
    )
    grouped["PULocationID"] = grouped["PULocationID"].astype(int)
    grouped["DOLocationID"] = grouped["DOLocationID"].astype(int)
    return grouped


def estimate_average_speed_mph(od_hist: pd.DataFrame) -> float:
    valid = od_hist[
        (od_hist["historical_distance"] > 0) & (od_hist["historical_duration"] > 0)
    ].copy()
    speed = valid["historical_distance"] / (valid["historical_duration"] / 60.0)
    speed = speed[(speed >= 3) & (speed <= 45)]
    if speed.empty:
        return 12.0
    return float(speed.median())


def build_od_reference(paths: Dict = None) -> pd.DataFrame:
    paths = paths or load_paths()
    root = get_project_root(paths)
    interim = root / paths["data"]["interim"]
    yellow = pd.read_parquet(interim / "yellow_clean.parquet")
    green = pd.read_parquet(interim / "green_clean.parquet")
    fhv = pd.read_parquet(interim / "fhv_clean.parquet")
    od_hist = historical_od_reference(yellow, green)
    centroids = load_zone_centroids(paths)
    avg_speed = estimate_average_speed_mph(od_hist)

    brooklyn_ids = sorted(brooklyn_location_ids(paths))
    required_pairs = set(product(brooklyn_ids, brooklyn_ids))
    required_pairs.update(
        zip(fhv["PULocationID"].astype(int), fhv["DOLocationID"].astype(int))
    )
    hist_pairs = set(zip(od_hist["PULocationID"], od_hist["DOLocationID"]))
    all_pairs = sorted(required_pairs | hist_pairs)
    pair_df = pd.DataFrame(all_pairs, columns=["PULocationID", "DOLocationID"])
    ref = pair_df.merge(od_hist, on=["PULocationID", "DOLocationID"], how="left")
    ref["n_samples"] = ref["n_samples"].fillna(0).astype(int)
    ref["centroid_distance"] = [
        centroid_distance_miles(pu, do, centroids)
        for pu, do in zip(ref["PULocationID"], ref["DOLocationID"])
    ]
    ref["fallback_distance"] = (ref["centroid_distance"] * 1.3).clip(lower=0.5)
    ref["fallback_duration"] = (ref["fallback_distance"] / avg_speed * 60.0).clip(
        lower=2.0
    )
    use_hist = (
        ref["n_samples"].ge(3)
        & ref["historical_distance"].gt(0)
        & ref["historical_duration"].gt(0)
    )
    ref["estimated_distance"] = np.where(
        use_hist, ref["historical_distance"], ref["fallback_distance"]
    )
    ref["estimated_duration"] = np.where(
        use_hist, ref["historical_duration"], ref["fallback_duration"]
    )
    ref["source"] = np.where(use_hist, "historical_median", "centroid_fallback")
    return ref[
        [
            "PULocationID",
            "DOLocationID",
            "n_samples",
            "estimated_distance",
            "estimated_duration",
            "source",
            "historical_distance",
            "historical_duration",
            "centroid_distance",
        ]
    ]


def write_od_outputs(paths: Dict = None):
    paths = paths or load_paths()
    root = get_project_root(paths)
    ref = build_od_reference(paths)
    ref_path = output_path("node08_od_reference", paths)
    ref.to_csv(ref_path, index=False, encoding="utf-8-sig")

    fhv = pd.read_parquet(root / paths["data"]["interim"] / "fhv_clean.parquet")
    enriched = fhv.merge(
        ref[
            [
                "PULocationID",
                "DOLocationID",
                "estimated_distance",
                "estimated_duration",
                "source",
            ]
        ],
        on=["PULocationID", "DOLocationID"],
        how="left",
    )
    enriched = enriched.rename(
        columns={
            "duration_min": "observed_duration_min",
            "estimated_duration": "estimated_od_duration_min",
            "source": "distance_source",
        }
    )
    fhv_path = output_path("node08_fhv_distance", paths)
    enriched.to_csv(fhv_path, index=False, encoding="utf-8-sig")
    return ref_path
