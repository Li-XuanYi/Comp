"""Shared schema constants for the node-based modeling workflow."""

from typing import Dict, List


RAW_DATASETS: List[str] = ["yellow", "green", "fhv"]
NODE01_DATASETS: List[str] = [
    "yellow",
    "green",
    "fhv",
    "taxi_zone_lookup",
    "taxi_zones_shp",
]

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

NODE01_AUDIT_COLUMNS: List[str] = [
    "dataset",
    "n_rows",
    "n_cols",
    "columns",
    "missing_rate_summary",
    "datetime_min",
    "datetime_max",
]
