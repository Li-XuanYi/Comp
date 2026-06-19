"""Node 11 three-base location optimization."""

from itertools import combinations
import os
from typing import Dict, Iterable, List, Sequence, Tuple

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

os.environ.setdefault("OMP_NUM_THREADS", "1")
from sklearn.cluster import KMeans

from src.io_utils import get_project_root, load_paths, output_path, resolve_config_path
from src.od_estimation import load_zone_centroids


def weighted_assignment_cost(
    time_matrix: pd.DataFrame, demand_zones: Sequence[int], weights: np.ndarray, bases: Sequence[int]
) -> Tuple[float, np.ndarray]:
    sub = time_matrix.loc[list(demand_zones), list(bases)].to_numpy(dtype=float)
    nearest_idx = np.argmin(sub, axis=1)
    nearest_time = sub[np.arange(len(demand_zones)), nearest_idx]
    return float(np.sum(weights * nearest_time)), nearest_idx


def enumerate_best_bases(time_matrix: pd.DataFrame, zones: Sequence[int], weights: np.ndarray) -> Tuple[Tuple[int, int, int], float]:
    best_bases = None
    best_cost = float("inf")
    for bases in combinations(zones, 3):
        cost, _ = weighted_assignment_cost(time_matrix, zones, weights, bases)
        if cost < best_cost:
            best_cost = cost
            best_bases = bases
    return tuple(best_bases), best_cost


def build_time_matrix(paths: Dict = None, zones: Sequence[int] = None) -> pd.DataFrame:
    paths = paths or load_paths()
    root = get_project_root(paths)
    ref = pd.read_csv(root / paths["node_outputs"]["node08_od_reference"])
    if zones is None:
        zones = sorted(pd.read_csv(root / paths["node_outputs"]["node10_vehicle_allocation"])["zone_id"].astype(int))
    matrix = ref.pivot_table(
        index="PULocationID", columns="DOLocationID", values="estimated_duration", aggfunc="min"
    )
    matrix = matrix.reindex(index=zones, columns=zones)
    fallback = float(ref["estimated_duration"].median())
    matrix = matrix.fillna(fallback)
    return matrix


def kmeans_base_zones(zones: Sequence[int], paths: Dict = None) -> Tuple[int, int, int]:
    centroids = load_zone_centroids(paths).set_index("LocationID").loc[list(zones)]
    kmeans = KMeans(n_clusters=3, random_state=20260619, n_init=10)
    labels = kmeans.fit_predict(centroids[["x", "y"]])
    selected = []
    for cluster in range(3):
        cluster_points = centroids.iloc[np.where(labels == cluster)[0]]
        center = kmeans.cluster_centers_[cluster]
        distances = ((cluster_points[["x", "y"]].to_numpy() - center) ** 2).sum(axis=1)
        selected.append(int(cluster_points.index[int(np.argmin(distances))]))
    return tuple(sorted(selected))


def optimize_base_locations(paths: Dict = None):
    paths = paths or load_paths()
    root = get_project_root(paths)
    allocation = pd.read_csv(root / paths["node_outputs"]["node10_vehicle_allocation"])
    zones = allocation["zone_id"].astype(int).tolist()
    weights = (
        allocation["predicted_demand_12pm"].astype(float)
        * allocation["avg_profit"].astype(float).clip(lower=0.1)
    ).to_numpy()
    time_matrix = build_time_matrix(paths, zones)
    zone_names = allocation.set_index("zone_id")["zone_name"].to_dict()

    optimal_bases, optimal_cost = enumerate_best_bases(time_matrix, zones, weights)
    baseline_bases = tuple(
        allocation.sort_values("predicted_demand_12pm", ascending=False)
        .head(3)["zone_id"]
        .astype(int)
    )
    random_bases = tuple(sorted(pd.Series(zones).sample(3, random_state=20260619).astype(int)))
    kmeans_bases = kmeans_base_zones(zones, paths)

    scenarios = [
        ("optimal_p_median", optimal_bases),
        ("top_demand_3", baseline_bases),
        ("random_3", random_bases),
        ("geographic_kmeans_3", kmeans_bases),
    ]
    rows = []
    for scenario, bases in scenarios:
        cost, _ = weighted_assignment_cost(time_matrix, zones, weights, bases)
        rows.append(
            {
                "scenario": scenario,
                "base_zone_ids": ";".join(str(int(base)) for base in bases),
                "base_zone_names": ";".join(zone_names.get(int(base), "") for base in bases),
                "weighted_dispatch_time_cost": cost,
                "improvement_vs_top_demand_pct": np.nan,
            }
        )
    result = pd.DataFrame(rows)
    top_cost = float(result.loc[result["scenario"] == "top_demand_3", "weighted_dispatch_time_cost"].iloc[0])
    result["improvement_vs_top_demand_pct"] = (top_cost - result["weighted_dispatch_time_cost"]) / top_cost

    cost, nearest_idx = weighted_assignment_cost(time_matrix, zones, weights, optimal_bases)
    assignment = allocation[["zone_id", "zone_name", "predicted_demand_12pm", "avg_profit"]].copy()
    assignment["weight"] = weights
    assignment["assigned_base_id"] = [optimal_bases[idx] for idx in nearest_idx]
    assignment["assigned_base_name"] = assignment["assigned_base_id"].map(zone_names)
    assignment["dispatch_time_min"] = [
        time_matrix.loc[zone, base]
        for zone, base in zip(assignment["zone_id"], assignment["assigned_base_id"])
    ]
    return result, assignment


def plot_base_location_map(assignment: pd.DataFrame, destination, paths: Dict = None) -> None:
    import shapefile  # type: ignore

    bases = sorted(assignment["assigned_base_id"].unique())
    base_to_color = {base: idx for idx, base in enumerate(bases)}
    shp_path = resolve_config_path("raw_inputs", "taxi_zones_shp", paths)
    reader = shapefile.Reader(str(shp_path))
    fields = [field[0] for field in reader.fields if field[0] != "DeletionFlag"]
    assignment_lookup = assignment.set_index("zone_id")["assigned_base_id"].to_dict()
    centroids = load_zone_centroids(paths).set_index("LocationID")
    cmap = plt.get_cmap("Set2")
    fig, ax = plt.subplots(figsize=(7, 7))
    for shape, record in zip(reader.shapes(), reader.records()):
        attrs = dict(zip(fields, record))
        if attrs.get("borough") != "Brooklyn":
            continue
        zone_id = int(attrs["LocationID"])
        base = assignment_lookup.get(zone_id)
        color = cmap(base_to_color.get(base, 0) / max(len(bases), 1))
        points = shape.points
        parts = list(shape.parts) + [len(points)]
        for start, end in zip(parts[:-1], parts[1:]):
            xs = [point[0] for point in points[start:end]]
            ys = [point[1] for point in points[start:end]]
            ax.fill(xs, ys, facecolor=color, edgecolor="#555555", linewidth=0.25)
    for base in bases:
        row = centroids.loc[base]
        ax.scatter(row["x"], row["y"], s=80, c="black", marker="o")
        ax.text(row["x"], row["y"], str(base), fontsize=8, color="white", ha="center", va="center")
    ax.set_title("Three optimal Brooklyn base zones")
    ax.set_axis_off()
    plt.tight_layout()
    plt.savefig(destination, dpi=160)
    plt.close()


def write_base_location_outputs(paths: Dict = None):
    paths = paths or load_paths()
    root = get_project_root(paths)
    result, assignment = optimize_base_locations(paths)
    result_path = output_path("node11_base_results", paths)
    assignment_path = output_path("node11_base_assignment", paths)
    result.to_csv(result_path, index=False, encoding="utf-8-sig")
    assignment.to_csv(assignment_path, index=False, encoding="utf-8-sig")
    fig_path = root / paths["outputs"]["figures"] / "base_location_map.png"
    plot_base_location_map(assignment, fig_path, paths)
    return result_path
