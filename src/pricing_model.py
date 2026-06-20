"""Node 09 FHV pricing using taxi reference fares."""

from typing import Dict, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.model_selection import train_test_split

from src.io_utils import get_project_root, load_paths, output_path
from src.metrics import mae, rmse, smape
from src.weather_calendar import calendar_features, load_or_create_weather


PRICE_FEATURES = [
    "distance",
    "duration_min",
    "PULocationID",
    "DOLocationID",
    "hour",
    "weekday",
    "is_weekend",
    "temperature",
    "precipitation",
    "snow_indicator",
    "wind_speed",
    "visibility",
]


def build_taxi_price_training_frame(paths: Dict = None) -> pd.DataFrame:
    paths = paths or load_paths()
    root = get_project_root(paths)
    interim = root / paths["data"]["interim"]
    yellow = pd.read_parquet(interim / "yellow_clean.parquet")
    green = pd.read_parquet(interim / "green_clean.parquet")
    taxi = pd.concat([yellow, green], ignore_index=True)
    taxi = taxi[
        [
            "pickup_datetime",
            "PULocationID",
            "DOLocationID",
            "trip_distance",
            "duration_min",
            "total_amount",
        ]
    ].rename(columns={"trip_distance": "distance"})
    taxi["pickup_datetime"] = pd.to_datetime(taxi["pickup_datetime"])
    taxi["datetime_hour"] = taxi["pickup_datetime"].dt.floor("H")
    taxi["hour"] = taxi["datetime_hour"].dt.hour
    cal = calendar_features(taxi["datetime_hour"])
    taxi["weekday"] = cal["weekday"].values
    taxi["is_weekend"] = cal["is_weekend"].values
    weather = load_or_create_weather(paths).drop(columns=["weather_source"], errors="ignore")
    taxi = taxi.merge(weather, on="datetime_hour", how="left")
    taxi[["temperature", "precipitation", "snow_indicator", "wind_speed", "visibility"]] = taxi[
        ["temperature", "precipitation", "snow_indicator", "wind_speed", "visibility"]
    ].fillna(
        taxi[["temperature", "precipitation", "snow_indicator", "wind_speed", "visibility"]].median(
            numeric_only=True
        )
    )
    taxi = taxi[
        (taxi["distance"] > 0)
        & (taxi["duration_min"] > 0)
        & (taxi["total_amount"] > 0)
        & (taxi["total_amount"] <= 300)
    ].copy()
    return taxi


def train_reference_price_model(taxi: pd.DataFrame) -> Tuple[HistGradientBoostingRegressor, Dict[str, float]]:
    sample = taxi.sample(n=min(len(taxi), 120000), random_state=20260619)
    train, valid = train_test_split(sample, test_size=0.2, random_state=20260619)
    model = HistGradientBoostingRegressor(
        loss="squared_error",
        learning_rate=0.06,
        max_iter=180,
        max_leaf_nodes=31,
        l2_regularization=0.05,
        random_state=20260619,
    )
    model.fit(train[PRICE_FEATURES], train["total_amount"])
    pred = np.clip(model.predict(valid[PRICE_FEATURES]), 0, None)
    metrics = {
        "reference_MAE": mae(valid["total_amount"], pred),
        "reference_RMSE": rmse(valid["total_amount"], pred),
        "reference_SMAPE": smape(valid["total_amount"], pred),
        "training_rows": int(len(sample)),
    }
    return model, metrics


def build_fhv_pricing_frame(paths: Dict = None) -> pd.DataFrame:
    paths = paths or load_paths()
    root = get_project_root(paths)
    fhv = pd.read_csv(root / paths["node_outputs"]["node08_fhv_distance"])
    fhv["pickup_datetime"] = pd.to_datetime(fhv["pickup_datetime"])
    fhv["distance"] = fhv["estimated_distance"]
    fhv["duration_min"] = fhv["observed_duration_min"].fillna(
        fhv["estimated_od_duration_min"]
    )
    fhv["datetime_hour"] = fhv["pickup_datetime"].dt.floor("H")
    fhv["hour"] = fhv["datetime_hour"].dt.hour
    cal = calendar_features(fhv["datetime_hour"])
    fhv["weekday"] = cal["weekday"].values
    fhv["is_weekend"] = cal["is_weekend"].values
    weather = load_or_create_weather(paths).drop(columns=["weather_source"], errors="ignore")
    fhv = fhv.merge(weather, on="datetime_hour", how="left")
    fhv[["temperature", "precipitation", "snow_indicator", "wind_speed", "visibility"]] = fhv[
        ["temperature", "precipitation", "snow_indicator", "wind_speed", "visibility"]
    ].fillna(
        fhv[["temperature", "precipitation", "snow_indicator", "wind_speed", "visibility"]].median(
            numeric_only=True
        )
    )
    return fhv


def price_fhv_orders(paths: Dict = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
    paths = paths or load_paths()
    taxi = build_taxi_price_training_frame(paths)
    model, metrics = train_reference_price_model(taxi)
    fhv = build_fhv_pricing_frame(paths)
    taxi_reference = np.clip(model.predict(fhv[PRICE_FEATURES]), 2.5, None)
    c0 = 2.75
    c_distance = 1.15
    c_time = 0.18
    minimum_profit_rate = 0.15
    discount_rate = 0.08
    shared_factor = 0.90

    cost = c0 + c_distance * fhv["distance"] + c_time * fhv["duration_min"]
    price_floor = cost * (1 + minimum_profit_rate)
    competitive_price = taxi_reference * (1 - discount_rate)
    fhv_price = np.maximum(price_floor, competitive_price)
    shared_mask = fhv["SR_Flag"].fillna(0).astype(float).eq(1)
    fhv_price = np.where(shared_mask, fhv_price * shared_factor, fhv_price)
    fhv_price = np.maximum(fhv_price, price_floor)

    result = fhv.copy()
    result["taxi_reference_price"] = taxi_reference
    result["estimated_cost"] = cost
    result["fhv_price"] = np.round(fhv_price, 2)
    result["estimated_profit"] = result["fhv_price"] - result["estimated_cost"]
    result["estimated_profit_rate"] = result["estimated_profit"] / result["estimated_cost"]

    summary = pd.DataFrame(
        [
            {
                "model": "hist_gradient_boosting_reference_price",
                **metrics,
                "fhv_rows": int(len(result)),
                "avg_taxi_reference_price": float(result["taxi_reference_price"].mean()),
                "avg_fhv_price": float(result["fhv_price"].mean()),
                "avg_estimated_cost": float(result["estimated_cost"].mean()),
                "avg_estimated_profit_rate": float(result["estimated_profit_rate"].mean()),
            }
        ]
    )
    return result, summary


def write_pricing_outputs(paths: Dict = None):
    paths = paths or load_paths()
    result, summary = price_fhv_orders(paths)
    result_path = output_path("node09_fhv_pricing", paths)
    summary_path = output_path("node09_pricing_summary", paths)
    result.to_csv(result_path, index=False, encoding="utf-8-sig")
    summary.to_csv(summary_path, index=False, encoding="utf-8-sig")
    return result_path
