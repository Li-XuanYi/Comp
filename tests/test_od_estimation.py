import pandas as pd

from src.od_estimation import estimate_average_speed_mph


def test_estimate_average_speed_mph_uses_historical_values():
    od = pd.DataFrame(
        {
            "historical_distance": [2.0, 4.0],
            "historical_duration": [10.0, 20.0],
        }
    )
    assert estimate_average_speed_mph(od) == 12.0

