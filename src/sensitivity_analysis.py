"""Post-node rigor enhancements: sensitivity analysis tables."""

from typing import Dict, Iterable, Tuple

import numpy as np
import pandas as pd

from src.dispatch_optimization import optimize_vehicle_allocation
from src.io_utils import get_project_root, load_paths, output_path


def pricing_parameter_sensitivity(paths: Dict = None) -> pd.DataFrame:
    paths = paths or load_paths()
    root = get_project_root(paths)
    pricing = pd.read_csv(root / paths["node_outputs"]["node09_fhv_pricing"])
    rows = []
    for minimum_profit_rate in [0.10, 0.15, 0.20]:
        for discount_rate in [0.05, 0.08, 0.12]:
            price_floor = pricing["estimated_cost"] * (1 + minimum_profit_rate)
            competitive = pricing["taxi_reference_price"] * (1 - discount_rate)
            price = np.maximum(price_floor, competitive)
            shared_mask = pricing["SR_Flag"].fillna(0).astype(float).eq(1)
            price = np.where(shared_mask, price * 0.90, price)
            price = np.maximum(price, price_floor * 0.95)
            profit_rate = (price - pricing["estimated_cost"]) / pricing["estimated_cost"]
            rows.append(
                {
                    "analysis_type": "pricing_parameters",
                    "parameter": "minimum_profit_rate={},discount_rate={}".format(
                        minimum_profit_rate, discount_rate
                    ),
                    "avg_fhv_price": float(np.mean(price)),
                    "avg_profit_rate": float(np.mean(profit_rate)),
                    "estimated_incremental_revenue": np.nan,
                    "estimated_incremental_profit": np.nan,
                }
            )
    return pd.DataFrame(rows)


def vehicle_count_sensitivity(paths: Dict = None) -> pd.DataFrame:
    paths = paths or load_paths()
    vehicle_counts = [25, 50, 75, 100, 150, 200, 250]
    _, summary = optimize_vehicle_allocation(paths, vehicle_counts)
    return pd.DataFrame(
        {
            "analysis_type": "vehicle_count",
            "parameter": "N=" + summary["vehicle_count"].astype(str),
            "avg_fhv_price": np.nan,
            "avg_profit_rate": np.nan,
            "estimated_incremental_revenue": summary["estimated_incremental_revenue"],
            "estimated_incremental_profit": summary["estimated_incremental_profit"],
        }
    )


def build_sensitivity_analysis(paths: Dict = None) -> pd.DataFrame:
    paths = paths or load_paths()
    return pd.concat(
        [pricing_parameter_sensitivity(paths), vehicle_count_sensitivity(paths)],
        ignore_index=True,
    )


def write_sensitivity_analysis(paths: Dict = None):
    paths = paths or load_paths()
    table = build_sensitivity_analysis(paths)
    path = output_path("rigor_sensitivity_analysis", paths)
    table.to_csv(path, index=False, encoding="utf-8-sig")
    return path

