import pandas as pd

from src.weather_calendar import build_weather_template, calendar_features


def test_weather_template_covers_target_day():
    weather = build_weather_template()
    assert weather["datetime_hour"].min() == pd.Timestamp("2019-01-01 00:00:00")
    assert weather["datetime_hour"].max() == pd.Timestamp("2019-02-01 23:00:00")
    assert {"temperature", "precipitation", "weather_source"}.issubset(weather.columns)


def test_calendar_features_peak_flags():
    values = pd.Series(pd.to_datetime(["2019-01-01 08:00:00", "2019-01-01 23:00:00"]))
    features = calendar_features(values)
    assert features.loc[0, "is_morning_peak"] == 1
    assert features.loc[1, "is_night"] == 1

