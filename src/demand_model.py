"""Node 07 main hourly demand prediction model."""

from typing import Dict, List, Tuple

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

from src.demand_baseline import TRAIN_END, VALID_END, evaluate_baselines
from src.io_utils import get_project_root, load_paths, output_path, read_taxi_zone_lookup
from src.metrics import mae, rmse, smape
from src.weather_calendar import calendar_features, load_or_create_weather


MODEL_FEATURES = [
    "zone_id",
    "hour",
    "weekday",
    "is_weekend",
    "is_holiday",
    "is_morning_peak",
    "is_evening_peak",
    "is_night",
    "hour_sin",
    "hour_cos",
    "temperature",
    "precipitation",
    "snow_indicator",
    "wind_speed",
    "visibility",
    "lag_24",
    "lag_168",
    "rolling_24_mean",
    "rolling_168_mean",
]


def add_lag_features(features: pd.DataFrame) -> pd.DataFrame:
    df = features.sort_values(["zone_id", "datetime_hour"]).copy()
    group = df.groupby("zone_id")["pickup_count"]
    df["lag_24"] = group.shift(24)
    df["lag_168"] = group.shift(168)
    df["rolling_24_mean"] = group.transform(
        lambda series: series.shift(1).rolling(24, min_periods=1).mean()
    )
    df["rolling_168_mean"] = group.transform(
        lambda series: series.shift(1).rolling(168, min_periods=1).mean()
    )
    zone_mean = df.groupby("zone_id")["pickup_count"].transform("mean")
    for column in ["lag_24", "lag_168", "rolling_24_mean", "rolling_168_mean"]:
        df[column] = df[column].fillna(zone_mean).fillna(df["pickup_count"].mean())
    return df


def train_validation_frames(features: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    modeled = add_lag_features(features)
    train = modeled[modeled["datetime_hour"] < TRAIN_END].copy()
    valid = modeled[
        (modeled["datetime_hour"] >= TRAIN_END) & (modeled["datetime_hour"] < VALID_END)
    ].copy()
    return train, valid


def train_main_model(train: pd.DataFrame) -> HistGradientBoostingRegressor:
    model = HistGradientBoostingRegressor(
        loss="poisson",
        learning_rate=0.06,
        max_iter=160,
        max_leaf_nodes=31,
        l2_regularization=0.05,
        random_state=20260619,
    )
    model.fit(train[MODEL_FEATURES], train["pickup_count"])
    return model


def build_future_frame(features: pd.DataFrame, paths: Dict = None) -> pd.DataFrame:
    paths = paths or load_paths()
    lookup = read_taxi_zone_lookup(paths)
    brooklyn = lookup[lookup["Borough"].astype(str).str.lower() == "brooklyn"][
        ["LocationID", "Zone", "Borough"]
    ].rename(columns={"LocationID": "zone_id", "Zone": "zone_name"})
    hours = pd.date_range("2019-02-01 00:00:00", "2019-02-01 23:00:00", freq="H")
    future = pd.MultiIndex.from_product(
        [sorted(brooklyn["zone_id"].astype(int)), hours], names=["zone_id", "datetime_hour"]
    ).to_frame(index=False)
    future = future.merge(brooklyn, on="zone_id", how="left")
    weather = load_or_create_weather(paths)
    future = future.merge(weather, on="datetime_hour", how="left")
    cal = calendar_features(future["datetime_hour"])
    future = pd.concat([future.reset_index(drop=True), cal], axis=1)
    future["hour"] = future["datetime_hour"].dt.hour

    hist = features.copy()
    hist["datetime_hour"] = pd.to_datetime(hist["datetime_hour"])
    lag_24 = hist[["zone_id", "datetime_hour", "pickup_count"]].copy()
    lag_24["datetime_hour"] = lag_24["datetime_hour"] + pd.Timedelta(days=1)
    lag_24 = lag_24.rename(columns={"pickup_count": "lag_24"})
    lag_168 = hist[["zone_id", "datetime_hour", "pickup_count"]].copy()
    lag_168["datetime_hour"] = lag_168["datetime_hour"] + pd.Timedelta(days=7)
    lag_168 = lag_168.rename(columns={"pickup_count": "lag_168"})
    future = future.merge(lag_24, on=["zone_id", "datetime_hour"], how="left")
    future = future.merge(lag_168, on=["zone_id", "datetime_hour"], how="left")
    zone_roll = (
        hist.sort_values("datetime_hour")
        .groupby("zone_id")
        .tail(168)
        .groupby("zone_id")["pickup_count"]
        .agg(rolling_24_mean=lambda x: x.tail(24).mean(), rolling_168_mean="mean")
        .reset_index()
    )
    future = future.merge(zone_roll, on="zone_id", how="left")
    zone_mean = hist.groupby("zone_id")["pickup_count"].mean()
    for column in ["lag_24", "lag_168", "rolling_24_mean", "rolling_168_mean"]:
        future[column] = future[column].fillna(future["zone_id"].map(zone_mean)).fillna(0)
    return future


def plot_validation_compare(valid: pd.DataFrame, prediction: np.ndarray, path) -> None:
    plot_df = valid[["datetime_hour", "pickup_count"]].copy()
    plot_df["prediction"] = prediction
    hourly = plot_df.groupby("datetime_hour", as_index=False).sum(numeric_only=True)
    plt.figure(figsize=(9, 4))
    plt.plot(hourly["datetime_hour"], hourly["pickup_count"], label="Actual", color="#1b9e77")
    plt.plot(hourly["datetime_hour"], hourly["prediction"], label="Model", color="#d95f02")
    plt.xlabel("Validation hour")
    plt.ylabel("Brooklyn pickups")
    plt.title("Validation demand: actual vs model prediction")
    plt.legend()
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()


def best_blend_prediction(model_pred, baseline_pred, y_true) -> Tuple[float, np.ndarray, float]:
    """Select the best convex blend weight for model predictions."""
    best_weight = 1.0
    best_pred = np.asarray(model_pred, dtype=float)
    best_mae = mae(y_true, best_pred)
    baseline_pred = np.asarray(baseline_pred, dtype=float)
    for weight in np.linspace(0.0, 1.0, 11):
        candidate = weight * best_pred + (1.0 - weight) * baseline_pred
        candidate_mae = mae(y_true, candidate)
        if candidate_mae < best_mae:
            best_weight = float(weight)
            best_mae = candidate_mae
            best_candidate = candidate
    if best_weight == 1.0:
        return best_weight, best_pred, best_mae
    return best_weight, best_candidate, best_mae


def future_zone_weekday_hour_baseline(features: pd.DataFrame, future: pd.DataFrame) -> pd.Series:
    table = features.groupby(["zone_id", "weekday", "hour"])["pickup_count"].mean()
    zone_hour = features.groupby(["zone_id", "hour"])["pickup_count"].mean()
    overall = float(features["pickup_count"].mean())
    pred = future.set_index(["zone_id", "weekday", "hour"]).index.map(table)
    pred = pd.Series(pred, index=future.index)
    fallback = future.set_index(["zone_id", "hour"]).index.map(zone_hour)
    fallback = pd.Series(fallback, index=future.index).fillna(overall)
    return pred.fillna(fallback).astype(float)


def write_main_model_outputs(paths: Dict = None):
    paths = paths or load_paths()
    root = get_project_root(paths)
    features = pd.read_parquet(root / paths["node_outputs"]["node04_hourly_features"])
    features["datetime_hour"] = pd.to_datetime(features["datetime_hour"])
    train, valid = train_validation_frames(features)
    model = train_main_model(train)
    gbdt_valid_pred = np.clip(model.predict(valid[MODEL_FEATURES]), 0, None)

    baseline_metrics, baseline_predictions = evaluate_baselines(features)
    best_baseline_mae = float(baseline_metrics["MAE"].min())
    baseline_valid_pred = baseline_predictions["zone_weekday_hour_mean"].to_numpy()
    blend_weight, valid_pred, blend_mae = best_blend_prediction(
        gbdt_valid_pred, baseline_valid_pred, valid["pickup_count"]
    )
    metrics = pd.DataFrame(
        [
            {
                "model": "hist_gradient_boosting_poisson_blend",
                "MAE": blend_mae,
                "RMSE": rmse(valid["pickup_count"], valid_pred),
                "SMAPE": smape(valid["pickup_count"], valid_pred),
                "best_baseline_MAE": best_baseline_mae,
                "gbdt_only_MAE": mae(valid["pickup_count"], gbdt_valid_pred),
                "gbdt_weight": blend_weight,
                "baseline_weight": 1.0 - blend_weight,
                "beats_best_baseline_mae": blend_mae <= best_baseline_mae,
            }
        ]
    )
    metrics_path = output_path("node07_model_metrics", paths)
    metrics.to_csv(metrics_path, index=False, encoding="utf-8-sig")

    future = build_future_frame(features, paths)
    gbdt_future_pred = np.clip(model.predict(future[MODEL_FEATURES]), 0, None)
    baseline_future_pred = future_zone_weekday_hour_baseline(features, future)
    future_pred = blend_weight * gbdt_future_pred + (1.0 - blend_weight) * baseline_future_pred
    prediction = future[["zone_id", "zone_name", "datetime_hour"]].copy()
    prediction["predicted_demand"] = future_pred
    prediction_path = output_path("node07_prediction", paths)
    prediction.to_csv(prediction_path, index=False, encoding="utf-8-sig")

    figure_path = root / paths["outputs"]["figures"] / "model_validation_compare.png"
    figure_path.parent.mkdir(parents=True, exist_ok=True)
    plot_validation_compare(valid, valid_pred, figure_path)
    return metrics_path
