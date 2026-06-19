import pandas as pd

from src.feature_engineering import build_hourly_demand_panel


def test_hourly_panel_output_if_clean_data_exists():
    panel = build_hourly_demand_panel()
    assert {"zone_id", "datetime_hour", "pickup_count"}.issubset(panel.columns)
    assert panel["pickup_count"].ge(0).all()
    assert panel["datetime_hour"].min() == pd.Timestamp("2019-01-01 00:00:00")
    assert panel["datetime_hour"].max() == pd.Timestamp("2019-01-31 23:00:00")

