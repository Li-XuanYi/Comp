"""Node 04 weather template and calendar feature construction."""

from typing import Dict
import json
import urllib.parse
import urllib.request

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


def fetch_open_meteo_weather() -> pd.DataFrame:
    """Fetch hourly historical weather for Brooklyn from Open-Meteo.

    The API is keyless and returns a reanalysis-based historical series. Values
    are requested in Fahrenheit, miles per hour, and inches to match the report
    narrative for NYC.
    """
    params = {
        "latitude": 40.6782,
        "longitude": -73.9442,
        "start_date": "2019-01-01",
        "end_date": "2019-02-01",
        "hourly": "temperature_2m,precipitation,snowfall,wind_speed_10m,visibility",
        "temperature_unit": "fahrenheit",
        "wind_speed_unit": "mph",
        "precipitation_unit": "inch",
        "timezone": "America/New_York",
    }
    url = "https://archive-api.open-meteo.com/v1/archive?" + urllib.parse.urlencode(
        params
    )
    with urllib.request.urlopen(url, timeout=30) as response:
        data = json.loads(response.read().decode("utf-8"))
    hourly = data["hourly"]
    weather = pd.DataFrame(
        {
            "datetime_hour": pd.to_datetime(hourly["time"]),
            "temperature": hourly["temperature_2m"],
            "precipitation": hourly["precipitation"],
            "snowfall": hourly["snowfall"],
            "wind_speed": hourly["wind_speed_10m"],
            "visibility": hourly["visibility"],
        }
    )
    for column in ["temperature", "precipitation", "snowfall", "wind_speed", "visibility"]:
        weather[column] = pd.to_numeric(weather[column], errors="coerce")
    weather[["temperature", "precipitation", "snowfall", "wind_speed"]] = weather[
        ["temperature", "precipitation", "snowfall", "wind_speed"]
    ].interpolate(limit_direction="both")
    # The archive endpoint may return visibility as an unavailable variable for
    # older reanalysis hours. Keep the real source for other weather fields and
    # use a neutral clear-weather value when visibility is unavailable.
    weather["visibility"] = weather["visibility"].fillna(16093.44)
    # Open-Meteo visibility is returned in meters. Convert to miles for a compact
    # model feature with interpretable NYC-scale values.
    weather["visibility"] = weather["visibility"] / 1609.344
    weather["snow_indicator"] = (
        (weather["snowfall"].fillna(0) > 0)
        | ((weather["temperature"] <= 32) & (weather["precipitation"] > 0))
    ).astype(int)
    weather["weather_source"] = "open_meteo_archive_api"
    return weather[
        [
            "datetime_hour",
            "temperature",
            "precipitation",
            "snow_indicator",
            "wind_speed",
            "visibility",
            "weather_source",
        ]
    ].round(
        {
            "temperature": 3,
            "precipitation": 4,
            "wind_speed": 3,
            "visibility": 3,
        }
    )


def load_or_create_weather(paths: Dict = None) -> pd.DataFrame:
    """Load real weather when available; fetch it when synthetic data is present."""
    weather_path = _node_output_path("node04_weather_hourly", paths)
    if weather_path.exists():
        existing = pd.read_csv(weather_path, parse_dates=["datetime_hour"])
        source = set(existing.get("weather_source", pd.Series(dtype=str)).dropna())
        required = ["temperature", "precipitation", "snow_indicator", "wind_speed", "visibility"]
        has_complete_required = (
            set(required).issubset(existing.columns) and not existing[required].isna().any().any()
        )
        if "open_meteo_archive_api" in source and has_complete_required:
            return existing
    try:
        weather = fetch_open_meteo_weather()
    except Exception:
        weather = build_weather_template(paths)
    weather.to_csv(weather_path, index=False, encoding="utf-8-sig")
    return weather


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
    weather = load_or_create_weather(paths)

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
