"""Node 10 noon vehicle allocation optimization."""

from typing import Dict, Iterable, Tuple

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.io_utils import get_project_root, load_paths, output_path, resolve_config_path


def zone_profit_service(pricing: pd.DataFrame) -> pd.DataFrame:
    pricing = pricing.copy()
    pricing["service_time"] = pricing["observed_duration_min"].fillna(
        pricing["estimated_od_duration_min"]
    )
    grouped = pricing.groupby("PULocationID").agg(
        avg_profit=("estimated_profit", "mean"),
        avg_revenue=("fhv_price", "mean"),
        avg_service_time=("service_time", "mean"),
    )
    return grouped.reset_index().rename(columns={"PULocationID": "zone_id"})


def allocate_greedy(zones: pd.DataFrame, total_vehicles: int) -> Tuple[np.ndarray, float, float]:
    vehicles = np.zeros(len(zones), dtype=int)
    served = np.zeros(len(zones), dtype=float)
    demand = zones["predicted_demand_12pm"].to_numpy(dtype=float)
    profit = zones["avg_profit"].to_numpy(dtype=float)
    revenue = zones["avg_revenue"].to_numpy(dtype=float)
    capacity = 60.0 / zones["avg_service_time"].clip(lower=3).to_numpy(dtype=float)

    for _ in range(total_vehicles):
        remaining = np.maximum(demand - served, 0)
        marginal_served = np.minimum(capacity, remaining)
        marginal_profit = marginal_served * profit
        idx = int(np.argmax(marginal_profit))
        vehicles[idx] += 1
        served[idx] += marginal_served[idx]

    total_profit = float(np.sum(np.minimum(served, demand) * profit))
    total_revenue = float(np.sum(np.minimum(served, demand) * revenue))
    return vehicles, total_revenue, total_profit


def plot_allocation_map(allocation: pd.DataFrame, destination, paths: Dict = None) -> None:
    import shapefile  # type: ignore

    values = allocation.set_index("zone_id")["vehicles_N100"].to_dict()
    max_value = max(values.values()) if values else 1
    shp_path = resolve_config_path("raw_inputs", "taxi_zones_shp", paths)
    reader = shapefile.Reader(str(shp_path))
    fields = [field[0] for field in reader.fields if field[0] != "DeletionFlag"]
    fig, ax = plt.subplots(figsize=(7, 7))
    cmap = plt.get_cmap("OrRd")
    for shape, record in zip(reader.shapes(), reader.records()):
        attrs = dict(zip(fields, record))
        if attrs.get("borough") != "Brooklyn":
            continue
        location_id = int(attrs["LocationID"])
        value = values.get(location_id, 0)
        color = cmap(value / max_value if max_value else 0)
        points = shape.points
        parts = list(shape.parts) + [len(points)]
        for start, end in zip(parts[:-1], parts[1:]):
            xs = [point[0] for point in points[start:end]]
            ys = [point[1] for point in points[start:end]]
            ax.fill(xs, ys, facecolor=color, edgecolor="#555555", linewidth=0.25)
    ax.set_title("Noon vehicle allocation, N=100")
    ax.set_axis_off()
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(vmin=0, vmax=max_value))
    sm.set_array([])
    fig.colorbar(sm, ax=ax, fraction=0.035, pad=0.02, label="Vehicles")
    plt.tight_layout()
    plt.savefig(destination, dpi=160)
    plt.close()


def optimize_vehicle_allocation(paths: Dict = None, vehicle_counts: Iterable[int] = (50, 100, 200)):
    paths = paths or load_paths()
    root = get_project_root(paths)
    demand = pd.read_csv(root / paths["node_outputs"]["node07_prediction"], parse_dates=["datetime_hour"])
    noon = demand[demand["datetime_hour"] == pd.Timestamp("2019-02-01 12:00:00")].copy()
    noon = noon.rename(columns={"predicted_demand": "predicted_demand_12pm"})
    pricing = pd.read_csv(root / paths["node_outputs"]["node09_fhv_pricing"])
    zone_stats = zone_profit_service(pricing)
    global_profit = float(pricing["estimated_profit"].mean())
    global_revenue = float(pricing["fhv_price"].mean())
    global_service = float(
        pricing["observed_duration_min"].fillna(pricing["estimated_od_duration_min"]).mean()
    )
    allocation = noon.merge(zone_stats, on="zone_id", how="left")
    allocation["avg_profit"] = allocation["avg_profit"].fillna(global_profit).clip(lower=0.5)
    allocation["avg_revenue"] = allocation["avg_revenue"].fillna(global_revenue).clip(lower=1.0)
    allocation["avg_service_time"] = allocation["avg_service_time"].fillna(global_service).clip(lower=3)

    summary_rows = []
    for count in vehicle_counts:
        vehicles, revenue, profit = allocate_greedy(allocation, int(count))
        allocation["vehicles_N{}".format(count)] = vehicles
        summary_rows.append(
            {
                "vehicle_count": int(count),
                "estimated_incremental_revenue": revenue,
                "estimated_incremental_profit": profit,
                "top_zone_id": int(allocation.iloc[int(np.argmax(vehicles))]["zone_id"]),
                "top_zone_name": allocation.iloc[int(np.argmax(vehicles))]["zone_name"],
            }
        )

    keep = [
        "zone_id",
        "zone_name",
        "predicted_demand_12pm",
        "avg_profit",
        "avg_service_time",
        "vehicles_N50",
        "vehicles_N100",
        "vehicles_N200",
    ]
    return allocation[keep], pd.DataFrame(summary_rows)


def write_dispatch_outputs(paths: Dict = None):
    paths = paths or load_paths()
    root = get_project_root(paths)
    allocation, summary = optimize_vehicle_allocation(paths)
    allocation_path = output_path("node10_vehicle_allocation", paths)
    summary_path = output_path("node10_revenue_gain_summary", paths)
    allocation.to_csv(allocation_path, index=False, encoding="utf-8-sig")
    summary.to_csv(summary_path, index=False, encoding="utf-8-sig")
    fig_path = root / paths["outputs"]["figures"] / "vehicle_allocation_map.png"
    plot_allocation_map(allocation, fig_path, paths)
    return allocation_path

