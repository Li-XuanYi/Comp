import pandas as pd

from src.dispatch_optimization import allocate_greedy


def test_allocate_greedy_respects_vehicle_count():
    zones = pd.DataFrame(
        {
            "predicted_demand_12pm": [10.0, 20.0],
            "avg_profit": [2.0, 5.0],
            "avg_revenue": [5.0, 8.0],
            "avg_service_time": [10.0, 10.0],
        }
    )
    vehicles, revenue, profit = allocate_greedy(zones, 5)
    assert vehicles.sum() == 5
    assert revenue >= 0
    assert profit >= 0

