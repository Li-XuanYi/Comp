from pathlib import Path

from src import PROJECT_NAME
from src.schema import RAW_DATASETS, RAW_INPUT_KEYS, REQUIRED_NODE00_PATHS


def test_project_package_imports():
    assert PROJECT_NAME == "nyc_fhv_dispatch"


def test_raw_dataset_keys_are_defined():
    assert RAW_DATASETS == ["yellow", "green", "fhv"]
    assert set(RAW_INPUT_KEYS) == set(RAW_DATASETS)


def test_node00_required_paths_exist():
    project_root = Path(__file__).resolve().parents[1]
    missing = [
        relative_path
        for relative_path in REQUIRED_NODE00_PATHS
        if not (project_root / relative_path).exists()
    ]
    assert missing == []

