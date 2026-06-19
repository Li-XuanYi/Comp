"""Validate node outputs for the NYC FHV dispatch project."""

import argparse
import importlib
import sys
from pathlib import Path
from typing import Callable, Dict, Iterable, List


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _failures_for_missing(paths: Iterable[str]) -> List[str]:
    failures = []
    for relative_path in paths:
        if not (PROJECT_ROOT / relative_path).exists():
            failures.append("missing: {}".format(relative_path))
    return failures


def check_node00() -> List[str]:
    """Check the initialization scaffold only."""
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
    required_files = [
        "README.md",
        "AGENTS.md",
        "Makefile",
        "requirements.txt",
        ".gitignore",
        "configs/paths.yaml",
        "configs/model.yaml",
        "configs/experiment.yaml",
        "src/__init__.py",
        "src/schema.py",
        "scripts/check_node.py",
        "scripts/run_node.py",
        "pytest.ini",
        "tests/test_schema.py",
    ]

    failures = _failures_for_missing(required_dirs)
    failures.extend(_failures_for_missing(required_files))

    sys.path.insert(0, str(PROJECT_ROOT))
    try:
        importlib.import_module("src")
        importlib.import_module("src.schema")
    except Exception as exc:  # pragma: no cover - reported by CLI.
        failures.append("src import failed: {}".format(exc))

    return failures


def check_not_implemented(node: str) -> List[str]:
    return [
        "{} is not implemented yet. Run nodes sequentially and complete earlier nodes first.".format(
            node
        )
    ]


CHECKS: Dict[str, Callable[[], List[str]]] = {
    "node00": check_node00,
}


def run_check(node: str) -> int:
    if node == "all":
        nodes = sorted(CHECKS)
    else:
        nodes = [node]

    all_failures = []
    for current_node in nodes:
        check = CHECKS.get(current_node)
        failures = check() if check else check_not_implemented(current_node)
        if failures:
            all_failures.append((current_node, failures))
        else:
            print("[PASS] {}".format(current_node))

    if all_failures:
        for failed_node, failures in all_failures:
            print("[FAIL] {}".format(failed_node))
            for failure in failures:
                print("  - {}".format(failure))
        return 1

    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate node outputs.")
    parser.add_argument("--node", required=True, help="Node id, for example node00.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    return run_check(args.node.lower())


if __name__ == "__main__":
    raise SystemExit(main())
