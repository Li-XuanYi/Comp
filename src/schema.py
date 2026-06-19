"""Shared schema constants for the node-based modeling workflow."""

from typing import Dict, List


RAW_DATASETS: List[str] = ["yellow", "green", "fhv"]

RAW_INPUT_KEYS: Dict[str, str] = {
    "yellow": "yellow_tripdata",
    "green": "green_tripdata",
    "fhv": "fhv_tripdata",
}

REQUIRED_NODE00_PATHS: List[str] = [
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
