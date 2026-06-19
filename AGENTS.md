# AGENTS.md

## Project

This repository solves the NYC for-hire vehicle dispatch decision modeling problem.

## Language

Use Python 3.10+ for final reproducible runs. Keep code compatible with the active local environment when possible.

## Development Rule

Work node by node. Do not implement future nodes unless explicitly requested.

## Data Rule

Do not modify original source attachments.
Do not commit large raw data files.
All generated tables should go to `outputs/tables/`.
All figures should go to `outputs/figures/`.
All trained models should go to `outputs/models/`.

## Validation Rule

After finishing a node, run:

```bash
python scripts/check_node.py --node NODE_ID
pytest -q
```

Only if both checks pass:

```bash
git status
git add src/ scripts/ tests/ configs/ outputs/tables/ outputs/figures/ README.md AGENTS.md Makefile requirements.txt .gitignore
git commit -m "nodeXX: short description"
git tag nodeXX-pass
```

If checks fail, fix the code and rerun checks. Do not commit failed work.

## Code Style

- Prefer Python modules over notebooks.
- Keep notebooks optional and exploratory.
- Use type hints where practical.
- Add docstrings for core functions.
- Keep random seeds fixed.
- Save every important intermediate result with clear filenames.
- Avoid hard-coded absolute paths.
- Read paths from `configs/paths.yaml`.

## Modeling Requirements

- Demand prediction must output hourly pickup counts for Brooklyn zones on 2019-02-01.
- Pricing must output a price for every row in the FHV file.
- Dispatch allocation must support configurable added vehicle numbers N.
- Base location must select exactly 3 Brooklyn zone IDs.

