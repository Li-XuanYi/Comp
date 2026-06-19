# NYC FHV Dispatch Modeling

This repository implements a node-by-node mathematical modeling workflow for the NYC for-hire vehicle dispatch decision problem.

The project follows the instructions in `CODEX_MODELING_MASTER_PROMPT.md`. Work should proceed one node at a time; each node must define its inputs, outputs, validation checks, and Git checkpoint.

## Problem Scope

The modeling task uses January 2019 NYC taxi and FHV records for Brooklyn-origin trips to answer four questions:

1. Forecast hourly pickup demand for each Brooklyn taxi zone on 2019-02-01.
2. Price each FHV order using yellow and green taxi fare patterns as reference.
3. Allocate additional vehicles across zones for noon on 2019-02-01.
4. Select exactly three Brooklyn base locations considering dispatch time, order volume, and profit.

## Project Layout

```text
configs/        Reproducible path, model, and experiment settings.
data/           Generated intermediate and processed data. Raw source files are not committed.
src/            Reusable modeling modules.
scripts/        Node runners, validation checks, and export scripts.
outputs/        Tables, figures, logs, models, and final submission artifacts.
tests/          Pytest checks for node-level logic.
```

## Node Workflow

Run a node check with:

```bash
python scripts/check_node.py --node node00
pytest -q
```

Only commit when both commands pass. Large raw attachments, generated caches, and model binaries should remain untracked.

