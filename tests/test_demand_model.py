from src.demand_model import MODEL_FEATURES


def test_model_features_include_lag_terms():
    assert "lag_24" in MODEL_FEATURES
    assert "lag_168" in MODEL_FEATURES
    assert "rolling_24_mean" in MODEL_FEATURES

