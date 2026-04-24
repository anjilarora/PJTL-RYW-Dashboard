# Ride YourWay — Inference Engine

ML scripts that export the production XGBoost model. The FastAPI backend loads that model from
`code/outputs/models/`; no training happens inside the backend image.

## Layout

| Path | Purpose |
|------|---------|
| `../config/pjtl_kpis_and_formulas.json` | Single source for the nine feature names, gate pass rules, thresholds, and Kent-Leg constants (shared with the FastAPI backend). |
| `src/` | `features.py`, loaders, plot helpers. |
| `scripts/sync_inputs_from_phase1.py` | Snapshots `code/intermediates/ (regenerable phase artifacts)` into `code/intermediates/inference_inputs/`. |
| `scripts/train_readiness_model_from_inputs.py` | Reads `code/intermediates/inference_inputs/readiness_training_base.csv`, writes the model to `code/outputs/models/`. |
| `scripts/test_readiness_edge_cases.py` | Slider-sensitivity contract, gates the export. |

This directory has no `inputs/`, `results/`, or `plots/` subfolders anymore —
all read/write targets sit under `code/intermediates/` and `code/outputs/` per
the folder contract (`code/inputs/` = `.xlsx`, `code/intermediates/` = CSV/JSON,
`code/outputs/` = models + plots + reports).

## Data pipeline (run from repo root)

```bash
python code/scripts/build_phase1_canonical_base.py        # code/inputs/*.xlsx -> code/intermediates/ (regenerable phase artifacts)*.csv
python code/scripts/generate_readiness_training_rows.py   # -> regenerated training rows CSV
python code/scripts/build_readiness_training_base.py      # -> code/intermediates/ (regenerable phase artifacts)readiness_training_base.csv
python code/inference_engine/scripts/sync_inputs_from_phase1.py
python code/inference_engine/scripts/train_readiness_model_from_inputs.py   # -> code/outputs/models/
```

Notebook and stage-level report artifacts were removed during repository cleanup.
Regenerate those artifacts only when needed, then prune again before shipping.

## Setup

```bash
cd code/inference_engine
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

## KPI and gate authority

`code/config/pjtl_kpis_and_formulas.json` (`schema_version`) is the versioned
contract for launch-readiness metrics, pass rules, and display strings.
Week-level reconstruction helpers live in `src/features.py`.
