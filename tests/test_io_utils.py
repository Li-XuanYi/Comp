import json
from pathlib import Path

import pandas as pd

from src.io_utils import (
    audit_dataframe,
    load_paths,
    read_taxi_zone_lookup,
    resolve_config_path,
)
from src.schema import NODE01_AUDIT_COLUMNS, NODE01_DATASETS


def test_resolve_config_path_finds_raw_inputs():
    paths = load_paths()
    yellow_path = resolve_config_path("raw_inputs", "yellow_tripdata", paths)
    assert yellow_path.exists()
    assert "yellow_tripdata" in yellow_path.name


def test_zone_lookup_reader_has_expected_columns():
    lookup = read_taxi_zone_lookup()
    assert {"LocationID", "Borough", "Zone"}.issubset(lookup.columns)
    assert len(lookup) > 0


def test_audit_dataframe_schema_and_datetime_bounds():
    df = pd.DataFrame(
        {
            "pickup_datetime": ["2019-01-01 00:00:00", "2019-01-02 01:00:00"],
            "value": [1.0, None],
        }
    )
    record = audit_dataframe("sample", df)
    assert list(record) == NODE01_AUDIT_COLUMNS
    assert record["n_rows"] == 2
    assert record["n_cols"] == 2
    assert json.loads(record["columns"]) == ["pickup_datetime", "value"]
    assert record["datetime_min"] == "2019-01-01 00:00:00"
    assert record["datetime_max"] == "2019-01-02 01:00:00"


def test_node01_dataset_contract():
    assert NODE01_DATASETS == [
        "yellow",
        "green",
        "fhv",
        "taxi_zone_lookup",
        "taxi_zones_shp",
    ]

