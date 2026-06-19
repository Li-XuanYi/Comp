"""Node 05 exploratory figures for the modeling report."""

from pathlib import Path
from typing import Dict

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from src.io_utils import get_project_root, load_paths, output_path, resolve_config_path


FIGURE_NAMES = [
    "brooklyn_total_demand_map.png",
    "hourly_pattern.png",
    "weekday_weekend_pattern.png",
    "weather_demand_relation.png",
    "top20_zones.png",
]


def _figure_dir(paths: Dict = None) -> Path:
    paths = paths or load_paths()
    root = get_project_root(paths)
    fig_dir = root / paths["outputs"]["figures"]
    fig_dir.mkdir(parents=True, exist_ok=True)
    return fig_dir


def _save_current(path: Path) -> None:
    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()


def plot_hourly_pattern(features: pd.DataFrame, destination: Path) -> None:
    hourly = features.groupby("hour", as_index=False)["pickup_count"].mean()
    plt.figure(figsize=(8, 4))
    plt.plot(hourly["hour"], hourly["pickup_count"], marker="o", color="#2c7fb8")
    plt.xlabel("Hour")
    plt.ylabel("Average pickups per zone")
    plt.title("Average hourly pickup pattern")
    plt.grid(alpha=0.25)
    _save_current(destination)


def plot_weekday_weekend_pattern(features: pd.DataFrame, destination: Path) -> None:
    grouped = (
        features.assign(day_type=lambda x: x["is_weekend"].map({0: "Weekday", 1: "Weekend"}))
        .groupby(["hour", "day_type"], as_index=False)["pickup_count"]
        .mean()
    )
    plt.figure(figsize=(8, 4))
    for label, sub in grouped.groupby("day_type"):
        plt.plot(sub["hour"], sub["pickup_count"], marker="o", label=label)
    plt.xlabel("Hour")
    plt.ylabel("Average pickups per zone")
    plt.title("Weekday vs weekend pickup pattern")
    plt.legend()
    plt.grid(alpha=0.25)
    _save_current(destination)


def plot_weather_relation(features: pd.DataFrame, destination: Path) -> None:
    weather = features.groupby("datetime_hour", as_index=False).agg(
        pickup_count=("pickup_count", "sum"), temperature=("temperature", "mean")
    )
    plt.figure(figsize=(7, 4))
    plt.scatter(weather["temperature"], weather["pickup_count"], s=18, alpha=0.65, color="#238b45")
    plt.xlabel("Temperature")
    plt.ylabel("Hourly Brooklyn pickups")
    plt.title("Weather-demand relation")
    plt.grid(alpha=0.2)
    _save_current(destination)


def plot_top20_zones(features: pd.DataFrame, destination: Path) -> None:
    top = (
        features.groupby(["zone_id", "zone_name"], as_index=False)["pickup_count"]
        .sum()
        .sort_values("pickup_count", ascending=False)
        .head(20)
        .sort_values("pickup_count")
    )
    plt.figure(figsize=(8, 7))
    plt.barh(top["zone_name"], top["pickup_count"], color="#756bb1")
    plt.xlabel("Total pickups")
    plt.title("Top 20 Brooklyn pickup zones")
    _save_current(destination)


def plot_brooklyn_demand_map(features: pd.DataFrame, destination: Path, paths: Dict = None) -> None:
    import shapefile  # type: ignore

    totals = features.groupby("zone_id")["pickup_count"].sum().to_dict()
    shp_path = resolve_config_path("raw_inputs", "taxi_zones_shp", paths)
    reader = shapefile.Reader(str(shp_path))
    fields = [field[0] for field in reader.fields if field[0] != "DeletionFlag"]
    max_value = max(totals.values()) if totals else 1

    fig, ax = plt.subplots(figsize=(7, 7))
    cmap = plt.get_cmap("YlGnBu")
    for shape, record in zip(reader.shapes(), reader.records()):
        attrs = dict(zip(fields, record))
        location_id = int(attrs["LocationID"])
        if attrs.get("borough") != "Brooklyn":
            continue
        value = totals.get(location_id, 0)
        color = cmap(value / max_value if max_value else 0)
        points = shape.points
        parts = list(shape.parts) + [len(points)]
        for start, end in zip(parts[:-1], parts[1:]):
            xs = [point[0] for point in points[start:end]]
            ys = [point[1] for point in points[start:end]]
            ax.fill(xs, ys, facecolor=color, edgecolor="#555555", linewidth=0.25)
    ax.set_title("Brooklyn total pickup demand")
    ax.set_axis_off()
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(vmin=0, vmax=max_value))
    sm.set_array([])
    fig.colorbar(sm, ax=ax, fraction=0.035, pad=0.02, label="Total pickups")
    _save_current(destination)


def generate_eda_outputs(paths: Dict = None) -> Path:
    paths = paths or load_paths()
    root = get_project_root(paths)
    features = pd.read_parquet(root / paths["node_outputs"]["node04_hourly_features"])
    fig_dir = _figure_dir(paths)

    plot_brooklyn_demand_map(features, fig_dir / FIGURE_NAMES[0], paths)
    plot_hourly_pattern(features, fig_dir / FIGURE_NAMES[1])
    plot_weekday_weekend_pattern(features, fig_dir / FIGURE_NAMES[2])
    plot_weather_relation(features, fig_dir / FIGURE_NAMES[3])
    plot_top20_zones(features, fig_dir / FIGURE_NAMES[4])

    top_zone = (
        features.groupby(["zone_id", "zone_name"], as_index=False)["pickup_count"]
        .sum()
        .sort_values("pickup_count", ascending=False)
        .iloc[0]
    )
    summary = pd.DataFrame(
        [
            {
                "total_pickups": int(features["pickup_count"].sum()),
                "n_zones": int(features["zone_id"].nunique()),
                "peak_hour": int(
                    features.groupby("hour")["pickup_count"].mean().idxmax()
                ),
                "top_zone_id": int(top_zone["zone_id"]),
                "top_zone_name": top_zone["zone_name"],
                "top_zone_pickups": int(top_zone["pickup_count"]),
                "figures": ";".join(FIGURE_NAMES),
            }
        ]
    )
    summary_path = output_path("node05_eda_summary", paths)
    summary.to_csv(summary_path, index=False, encoding="utf-8-sig")
    return summary_path

