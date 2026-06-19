"""Lightweight node runner.

Node 00 only verifies that the scaffold exists. Later nodes should add their own
implementation when they are reached.
"""

import argparse
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


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
    raise SystemExit(
        "{} is not implemented yet. Complete nodes sequentially.".format(args.node)
    )


if __name__ == "__main__":
    raise SystemExit(main())

