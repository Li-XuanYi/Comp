import numpy as np

from src.metrics import mae, rmse, smape


def test_metrics_are_finite():
    y_true = np.array([0, 2, 4])
    y_pred = np.array([0, 3, 3])
    assert mae(y_true, y_pred) >= 0
    assert rmse(y_true, y_pred) >= 0
    assert smape(y_true, y_pred) >= 0

