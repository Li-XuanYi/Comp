import pandas as pd

from src.demand_baseline import split_train_validation


def test_split_train_validation_uses_expected_dates():
    df = pd.DataFrame(
        {
            "datetime_hour": pd.to_datetime(["2019-01-24 23:00", "2019-01-25 00:00"]),
            "pickup_count": [1, 2],
        }
    )
    train, valid = split_train_validation(df)
    assert len(train) == 1
    assert len(valid) == 1

