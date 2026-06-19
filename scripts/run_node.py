"""Lightweight node runner.

Node 00 only verifies that the scaffold exists. Later nodes should add their own
implementation when they are reached.
"""

import argparse
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


def run_node00() -> None:
    required_dirs = [
        "configs",
        "data/raw",
        "data/interim",
        "data/processed",
        "data/external",
        "src",
        "scripts",
        "outputs/tables",
        "outputs/figures",
        "outputs/models",
        "outputs/logs",
        "outputs/submission",
        "tests",
    ]
    for relative_dir in required_dirs:
        (PROJECT_ROOT / relative_dir).mkdir(parents=True, exist_ok=True)
    print("node00 scaffold directories are present")


def run_node01() -> None:
    from src.io_utils import write_data_audit

    destination = write_data_audit()
    print("node01 data audit written to {}".format(destination))


def run_node02() -> None:
    from src.preprocessing import write_clean_outputs

    destination = write_clean_outputs()
    print("node02 cleaning report written to {}".format(destination))


def run_node03() -> None:
    from src.feature_engineering import write_hourly_demand_panel

    destination = write_hourly_demand_panel()
    print("node03 demand panel written to {}".format(destination))


def run_node04() -> None:
    from src.weather_calendar import write_hourly_features

    destination = write_hourly_features()
    print("node04 hourly features written to {}".format(destination))


def run_node05() -> None:
    from src.visualization import generate_eda_outputs

    destination = generate_eda_outputs()
    print("node05 EDA summary written to {}".format(destination))


def run_node06() -> None:
    from src.demand_baseline import write_baseline_outputs

    destination = write_baseline_outputs()
    print("node06 baseline metrics written to {}".format(destination))


def run_node07() -> None:
    from src.demand_model import write_main_model_outputs

    destination = write_main_model_outputs()
    print("node07 model metrics written to {}".format(destination))


def run_node08() -> None:
    from src.od_estimation import write_od_outputs

    destination = write_od_outputs()
    print("node08 OD reference written to {}".format(destination))


def run_node09() -> None:
    from src.pricing_model import write_pricing_outputs

    destination = write_pricing_outputs()
    print("node09 FHV pricing written to {}".format(destination))


def run_node10() -> None:
    from src.dispatch_optimization import write_dispatch_outputs

    destination = write_dispatch_outputs()
    print("node10 vehicle allocation written to {}".format(destination))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a modeling node.")
    parser.add_argument("--node", required=True, help="Node id, for example node00.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    node = args.node.lower()
    if node == "node00":
        run_node00()
        return 0
    if node == "node01":
        run_node01()
        return 0
    if node == "node02":
        run_node02()
        return 0
    if node == "node03":
        run_node03()
        return 0
    if node == "node04":
        run_node04()
        return 0
    if node == "node05":
        run_node05()
        return 0
    if node == "node06":
        run_node06()
        return 0
    if node == "node07":
        run_node07()
        return 0
    if node == "node08":
        run_node08()
        return 0
    if node == "node09":
        run_node09()
        return 0
    if node == "node10":
        run_node10()
        return 0
    raise SystemExit(
        "{} is not implemented yet. Complete nodes sequentially.".format(args.node)
    )


if __name__ == "__main__":
    raise SystemExit(main())
