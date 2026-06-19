"""Export final Excel attachments and summary for Node 12."""

from pathlib import Path
import shutil
import sys

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.io_utils import get_project_root, load_paths
from src.sensitivity_analysis import write_sensitivity_analysis


SUBMISSION_FILES = [
    "q1_hourly_prediction.xlsx",
    "q2_fhv_pricing.xlsx",
    "q3_vehicle_allocation.xlsx",
    "q4_base_location.xlsx",
    "sensitivity_analysis.xlsx",
    "model_summary.md",
]


def _path(paths, key):
    root = get_project_root(paths)
    path = root / paths["node_outputs"][key]
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def copy_figures(paths) -> None:
    root = get_project_root(paths)
    source_dir = root / paths["outputs"]["figures"]
    dest_dir = root / paths["outputs"]["submission"] / "figures"
    dest_dir.mkdir(parents=True, exist_ok=True)
    for figure in source_dir.glob("*.png"):
        if figure.stat().st_size > 0:
            shutil.copy2(figure, dest_dir / figure.name)


def build_model_summary(paths) -> str:
    root = get_project_root(paths)
    q1 = pd.read_csv(root / paths["node_outputs"]["node07_prediction"])
    q2 = pd.read_csv(root / paths["node_outputs"]["node09_fhv_pricing"])
    q4 = pd.read_csv(root / paths["node_outputs"]["node11_base_results"])
    node07_metrics = pd.read_csv(root / paths["node_outputs"]["node07_model_metrics"]).iloc[0]
    node09_summary = pd.read_csv(root / paths["node_outputs"]["node09_pricing_summary"]).iloc[0]
    node10_summary = pd.read_csv(root / paths["node_outputs"]["node10_revenue_gain_summary"])
    sensitivity = pd.read_csv(root / paths["node_outputs"]["rigor_sensitivity_analysis"])
    optimal = q4[q4["scenario"] == "optimal_p_median"].iloc[0]

    return "\n".join(
        [
            "# NYC FHV Dispatch Modeling Summary",
            "",
            "## Question 1: Hourly Demand Prediction",
            "Model: HistGradientBoosting Poisson model blended with the best historical baseline.",
            "Output: q1_hourly_prediction.xlsx with {} rows, {} zones, and 24 hours.".format(
                len(q1), q1["zone_id"].nunique()
            ),
            "Validation MAE: {:.4f}; RMSE: {:.4f}; best baseline MAE: {:.4f}.".format(
                node07_metrics["MAE"], node07_metrics["RMSE"], node07_metrics["best_baseline_MAE"]
            ),
            "",
            "## Question 2: FHV Pricing",
            "Model: Taxi reference price regression plus cost floor and minimum-profit constraint.",
            "Output: q2_fhv_pricing.xlsx with {} priced FHV orders.".format(len(q2)),
            "Average FHV price: {:.2f}; average cost-based profit rate: {:.2%}.".format(
                node09_summary["avg_fhv_price"], node09_summary["avg_estimated_profit_rate"]
            ),
            "",
            "## Question 3: Noon Vehicle Allocation",
            "Model: Greedy integer allocation by marginal profit, demand, and service capacity.",
            "Output: q3_vehicle_allocation.xlsx with N=50, 100, and 200 vehicle plans.",
            "Estimated incremental profit for N=100: {:.2f}.".format(
                node10_summary.loc[
                    node10_summary["vehicle_count"] == 100, "estimated_incremental_profit"
                ].iloc[0]
            ),
            "When predicted noon demand is fully covered, remaining vehicles are held idle/reserve; for N=200, {} vehicles are allocated and {} remain idle.".format(
                int(node10_summary.loc[node10_summary["vehicle_count"] == 200, "allocated_vehicles"].iloc[0]),
                int(node10_summary.loc[node10_summary["vehicle_count"] == 200, "idle_vehicles"].iloc[0]),
            ),
            "",
            "## Question 4: Three Base Locations",
            "Model: Exhaustive weighted p-median over Brooklyn zone triples.",
            "Output: q4_base_location.xlsx with selected bases and zone assignments.",
            "Optimal base zones: {} ({}) with business-value-weighted dispatch time {:.2f}.".format(
                optimal["base_zone_ids"],
                optimal["base_zone_names"],
                optimal["weighted_dispatch_time_cost"],
            ),
            "Feasibility note: zone-level base IDs identify service areas; the final physical depot should be placed on feasible parking or dispatch property inside the selected TLC zone.",
            "",
            "## Sensitivity Analysis",
            "Output: sensitivity_analysis.xlsx with {} scenarios covering vehicle counts and pricing parameters.".format(
                len(sensitivity)
            ),
            "The vehicle-count analysis reports N=25,50,75,100,150,200,250; pricing analysis varies minimum profit rate and competitive discount.",
            "",
            "## Assumptions",
            "- Weather features use Open-Meteo historical hourly reanalysis for Brooklyn when network access is available, with a deterministic template fallback for reproducibility.",
            "- OD pairs with insufficient taxi samples use centroid-distance fallback calibrated by historical average speed.",
            "- The baseline vehicle allocation treats taxi-origin demand as an upper-bound proxy for FHV-addressable demand; use rho < 1 for lower platform penetration.",
            "",
        ]
    )


def export_submission() -> None:
    paths = load_paths()
    root = get_project_root(paths)
    write_sensitivity_analysis(paths)
    q1 = pd.read_csv(root / paths["node_outputs"]["node07_prediction"])
    q2 = pd.read_csv(root / paths["node_outputs"]["node09_fhv_pricing"])
    q3 = pd.read_csv(root / paths["node_outputs"]["node10_vehicle_allocation"])
    q4_results = pd.read_csv(root / paths["node_outputs"]["node11_base_results"])
    q4_assignment = pd.read_csv(root / paths["node_outputs"]["node11_base_assignment"])
    sensitivity = pd.read_csv(root / paths["node_outputs"]["rigor_sensitivity_analysis"])
    feasibility = pd.DataFrame(
        [
            {
                "base_zone_id": int(zone_id),
                "base_zone_name": zone_name,
                "feasibility_note": "TLC zone-level base; choose a legal parking/dispatch facility inside the zone. Avoid interpreting the zone label as the exact depot parcel.",
            }
            for zone_id, zone_name in zip(
                str(q4_results.loc[q4_results["scenario"] == "optimal_p_median", "base_zone_ids"].iloc[0]).split(";"),
                str(q4_results.loc[q4_results["scenario"] == "optimal_p_median", "base_zone_names"].iloc[0]).split(";"),
            )
        ]
    )

    q1.to_excel(_path(paths, "node12_q1_prediction"), index=False)
    q2.to_excel(_path(paths, "node12_q2_pricing"), index=False)
    q3.to_excel(_path(paths, "node12_q3_allocation"), index=False)
    with pd.ExcelWriter(_path(paths, "node12_q4_base_location")) as writer:
        q4_results.to_excel(writer, sheet_name="base_results", index=False)
        q4_assignment.to_excel(writer, sheet_name="assignment", index=False)
        feasibility.to_excel(writer, sheet_name="feasibility_notes", index=False)
    sensitivity.to_excel(_path(paths, "rigor_sensitivity_submission"), index=False)

    _path(paths, "node12_model_summary").write_text(
        build_model_summary(paths), encoding="utf-8"
    )
    copy_figures(paths)
    print("submission outputs written to {}".format(root / paths["outputs"]["submission"]))


if __name__ == "__main__":
    export_submission()
