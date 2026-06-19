"""Node 04 weather template and calendar feature construction."""

from typing import Dict

import numpy as np
import pandas as pd

from src.io_utils import get_project_root, load_paths, output_path


def _node_output_path(key: str, paths: Dict = None):
    paths = paths or load_paths()
    root = get_project_root(paths)
    path = root / paths["node_outputs"][key]
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def build_weather_template(paths: Dict = None) -> pd.DataFrame:
    """Create a deterministic hourly weather template for Jan 2019 plus target day."""
    hours = pd.date_range("2019-01-01 00:00:00", "2019-02-01 23:00:00", freq="H")
    hour = hours.hour.to_numpy()
    day_index = (hours.dayofyear - hours.dayofyear.min()).to_numpy()
    temperature = 33 + 7 * np.sin(2 * np.pi * (hour - 6) / 24) + 4 * np.sin(
        2 * np.pi * day_index / 7
    )
    precipitation = np.where(
        (hours.dayofweek >= 5) & np.isin(hour, [8, 9, 17, 18]), 0.03, 0.0
    )
    snow_indicator = ((temperature < 32) & (precipitation > 0)).astype(int)
    wind_speed = 8 + 2 * np.cos(2 * np.pi * hour / 24)
    visibility = np.where(precipitation > 0, 7.0, 10.0)
    return pd.DataFrame(
        {
            "datetime_hour": hours,
            "temperature": np.round(temperature, 3),
            "precipitation": precipitation,
            "snow_indicator": snow_indicator,
            "wind_speed": np.round(wind_speed, 3),
            "visibility": visibility,
            "weather_source": "synthetic_template",
        }
    )


def calendar_features(datetime_hour: pd.Series) -> pd.DataFrame:
    dt = pd.to_datetime(datetime_hour)
    hour = dt.dt.hour
    weekday = dt.dt.weekday
    holidays = {pd.Timestamp("2019-01-01").date(), pd.Timestamp("2019-01-21").date()}
    return pd.DataFrame(
        {
            "weekday": weekday,
            "is_weekend": weekday.isin([5, 6]).astype(int),
            "is_holiday": dt.dt.date.isin(holidays).astype(int),
            "is_morning_peak": hour.between(7, 9).astype(int),
            "is_evening_peak": hour.between(16, 18).astype(int),
            "is_night": ((hour <= 5) | (hour >= 22)).astype(int),
            "hour_sin": np.sin(2 * np.pi * hour / 24),
            "hour_cos": np.cos(2 * np.pi * hour / 24),
            "month": dt.dt.month,
            "day": dt.dt.day,
        }
    )


def build_hourly_features(paths: Dict = None) -> pd.DataFrame:
    paths = paths or load_paths()
    root = get_project_root(paths)
    panel = pd.read_parquet(root / paths["node_outputs"]["node03_demand_panel"])
    weather_path = _node_output_path("node04_weather_hourly", paths)
    if weather_path.exists():
        weather = pd.read_csv(weather_path, parse_dates=["datetime_hour"])
    else:
        weather = build_weather_template(paths)
        weather.to_csv(weather_path, index=False, encoding="utf-8-sig")

    features = panel.drop(columns=["weekday", "is_weekend"], errors="ignore").merge(
        weather, on="datetime_hour", how="left"
    )
    cal = calendar_features(features["datetime_hour"])
    features = pd.concat([features.reset_index(drop=True), cal], axis=1)
    return features


def write_hourly_features(paths: Dict = None):
    paths = paths or load_paths()
    features = build_hourly_features(paths)
    feature_path = _node_output_path("node04_hourly_features", paths)
    features.to_parquet(feature_path, index=False)

    missing_rates = features.isna().mean()
    summary = pd.DataFrame(
        [
            {
                "n_rows": len(features),
                "n_cols": len(features.columns),
                "datetime_min": features["datetime_hour"].min(),
                "datetime_max": features["datetime_hour"].max(),
                "max_missing_rate": float(missing_rates.max()),
                "weather_source": features["weather_source"].mode().iloc[0],
            }
        ]
    )
    summary_path = output_path("node04_feature_summary", paths)
    summary.to_csv(summary_path, index=False, encoding="utf-8-sig")
    return feature_path
