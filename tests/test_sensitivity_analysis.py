from src.sensitivity_analysis import build_sensitivity_analysis


def test_sensitivity_analysis_has_two_analysis_types():
    table = build_sensitivity_analysis()
    assert {"pricing_parameters", "vehicle_count"}.issubset(set(table["analysis_type"]))

