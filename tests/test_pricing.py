import numpy as np

from src.metrics import mae, rmse, smape
from src.pricing_model import PRICE_FEATURES


def test_metrics_are_finite():
    y_true = np.array([0, 2, 4])
    y_pred = np.array([0, 3, 3])
    assert mae(y_true, y_pred) >= 0
    assert rmse(y_true, y_pred) >= 0
    assert smape(y_true, y_pred) >= 0


def test_price_features_include_trip_geometry_and_time():
    assert "distance" in PRICE_FEATURES
    assert "duration_min" in PRICE_FEATURES
    assert "PULocationID" in PRICE_FEATURES
    assert "hour" in PRICE_FEATURES
    assert "temperature" in PRICE_FEATURES
    assert "precipitation" in PRICE_FEATURES
