from scripts.export_submission import SUBMISSION_FILES


def test_submission_file_contract():
    assert SUBMISSION_FILES == [
        "q1_hourly_prediction.xlsx",
        "q2_fhv_pricing.xlsx",
        "q3_vehicle_allocation.xlsx",
        "q4_base_location.xlsx",
        "sensitivity_analysis.xlsx",
        "model_summary.md",
    ]
