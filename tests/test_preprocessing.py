import pandas as pd

from src.preprocessing import clean_trip_data, standardize_trip_columns


def test_standardize_yellow_columns_adds_duration():
    df = pd.DataFrame(
        {
            "tpep_pickup_datetime": ["2019-01-01 00:00:00"],
            "tpep_dropoff_datetime": ["2019-01-01 00:10:00"],
        }
    )
    out = standardize_trip_columns(df, "yellow")
    assert "pickup_datetime" in out.columns
    assert "dropoff_datetime" in out.columns
    assert out.loc[0, "duration_min"] == 10


def test_clean_trip_data_filters_invalid_taxi_rows():
    df = pd.DataFrame(
        {
            "tpep_pickup_datetime": ["2019-01-01 00:00:00", "2019-02-01 00:00:00"],
            "tpep_dropoff_datetime": ["2019-01-01 00:10:00", "2019-02-01 00:10:00"],
            "PULocationID": [1, 1],
            "trip_distance": [2.0, 2.0],
            "total_amount": [10.0, 10.0],
            "fare_amount": [8.0, 8.0],
        }
    )
    cleaned, report = clean_trip_data(df, "yellow", {1})
    assert len(cleaned) == 1
    assert report["removed_rows"] == 1

