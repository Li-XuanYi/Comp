from src.visualization import FIGURE_NAMES


def test_expected_eda_figure_names_are_stable():
    assert FIGURE_NAMES == [
        "brooklyn_total_demand_map.png",
        "hourly_pattern.png",
        "weekday_weekend_pattern.png",
        "weather_demand_relation.png",
        "top20_zones.png",
    ]

