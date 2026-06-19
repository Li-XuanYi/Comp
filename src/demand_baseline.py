"""Node 06 demand forecast baselines."""

from typing import Dict, List, Tuple

import pandas as pd

from src.io_utils import get_project_root, load_paths, output_path
from src.metrics import mae, rmse, smape


TRAIN_END = pd.Timestamp("2019-01-25 00:00:00")
VALID_END = pd.Timestamp("2019-02-01 00:00:00")


def split_train_validation(features: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    df = features.copy()
    df["datetime_hour"] = pd.to_datetime(df["datetime_hour"])
    train = df[df["datetime_hour"] < TRAIN_END].copy()
    valid = df[(df["datetime_hour"] >= TRAIN_END) & (df["datetime_hour"] < VALID_END)].copy()
    return train, valid


def _fallback_mean(train: pd.DataFrame) -> float:
    return float(train["pickup_count"].mean())


def predict_zone_hour_mean(train: pd.DataFrame, valid: pd.DataFrame) -> pd.Series:
    table = train.groupby(["zone_id", "hour"])["pickup_count"].mean()
    fallback = _fallback_mean(train)
    pred = valid.set_index(["zone_id", "hour"]).index.map(table)
    return pd.Series(pred, index=valid.index).fillna(fallback).astype(float)


def predict_zone_weekday_hour_mean(train: pd.DataFrame, valid: pd.DataFrame) -> pd.Series:
    table = train.groupby(["zone_id", "weekday", "hour"])["pickup_count"].mean()
    fallback = predict_zone_hour_mean(train, valid)
    pred = valid.set_index(["zone_id", "weekday", "hour"]).index.map(table)
    return pd.Series(pred, index=valid.index).fillna(pd.Series(fallback, index=valid.index)).astype(float)


def predict_recent_week_same_hour(train: pd.DataFrame, valid: pd.DataFrame) -> pd.Series:
    hist = train[["zone_id", "datetime_hour", "pickup_count"]].copy()
    hist["lookup_hour"] = hist["datetime_hour"] + pd.Timedelta(days=7)
    table = hist.set_index(["zone_id", "lookup_hour"])["pickup_count"]
    fallback = predict_zone_weekday_hour_mean(train, valid)
    pred = valid.set_index(["zone_id", "datetime_hour"]).index.map(table)
    return pd.Series(pred, index=valid.index).fillna(pd.Series(fallback, index=valid.index)).astype(float)


BASELINE_FUNCTIONS = {
    "zone_hour_mean": predict_zone_hour_mean,
    "zone_weekday_hour_mean": predict_zone_weekday_hour_mean,
    "recent_week_same_hour": predict_recent_week_same_hour,
}


def evaluate_baselines(features: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    train, valid = split_train_validation(features)
    prediction_frame = valid[
        ["zone_id", "zone_name", "datetime_hour", "pickup_count"]
    ].copy()
    metrics: List[Dict[str, float]] = []
    for name, func in BASELINE_FUNCTIONS.items():
        pred = func(train, valid).clip(lower=0)
        prediction_frame[name] = pred.values
        metrics.append(
            {
                "model": name,
                "MAE": mae(valid["pickup_count"], pred),
                "RMSE": rmse(valid["pickup_count"], pred),
                "SMAPE": smape(valid["pickup_count"], pred),
            }
        )
    return pd.DataFrame(metrics).sort_values("MAE"), prediction_frame


def write_baseline_outputs(paths: Dict = None):
    paths = paths or load_paths()
    root = get_project_root(paths)
    features = pd.read_parquet(root / paths["node_outputs"]["node04_hourly_features"])
    metrics_df, predictions = evaluate_baselines(features)
    metrics_path = output_path("node06_baseline_metrics", paths)
    pred_path = output_path("node06_baseline_validation_predictions", paths)
    metrics_df.to_csv(metrics_path, index=False, encoding="utf-8-sig")
    predictions.to_csv(pred_path, index=False, encoding="utf-8-sig")
    return metrics_path
