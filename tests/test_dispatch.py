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
    vehicles, revenue, profit, idle_vehicles, served_demand = allocate_greedy(zones, 5)
    assert vehicles.sum() + idle_vehicles == 5
    assert revenue >= 0
    assert profit >= 0
    assert served_demand >= 0


def test_allocate_greedy_keeps_vehicles_idle_after_demand_is_served():
    zones = pd.DataFrame(
        {
            "predicted_demand_12pm": [1.0],
            "avg_profit": [10.0],
            "avg_revenue": [12.0],
            "avg_service_time": [10.0],
        }
    )
    vehicles, revenue, profit, idle_vehicles, served_demand = allocate_greedy(zones, 5)
    assert vehicles.sum() == 1
    assert idle_vehicles == 4
    assert served_demand == 1.0
    assert revenue == 12.0
    assert profit == 10.0
