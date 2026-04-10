# Ride YourWay — Inference Engine

ML diagnostics, staged notebooks, and the training script that exports the
production XGBoost model. The FastAPI backend loads that model from
`code/outputs/models/`; no training happens inside the backend image.

## Layout

| Path | Purpose |
|------|---------|
| `../config/pjtl_kpis_and_formulas.json` | Single source for the nine feature names, gate pass rules, thresholds, and Kent-Leg constants (shared with the FastAPI backend). |
| `src/` | `features.py`, loaders, plot helpers. |
| `notebooks/stages/` | Stage 1 (EDA) → Stage 2 (diagnostics) → Stage 3 (export). |
| `scripts/sync_inputs_from_phase1.py` | Snapshots `code/intermediates/phase1/` into `code/intermediates/inference_inputs/`. |
| `scripts/train_readiness_model_from_inputs.py` | Reads `code/intermediates/inference_inputs/readiness_training_base.csv`, writes the model to `code/outputs/models/`. |
| `scripts/test_readiness_edge_cases.py` | Slider-sensitivity contract, gates the export. |

This directory has no `inputs/`, `results/`, or `plots/` subfolders anymore —
all read/write targets sit under `code/intermediates/` and `code/outputs/` per
the folder contract (`code/inputs/` = `.xlsx`, `code/intermediates/` = CSV/JSON,
`code/outputs/` = models + plots + reports).

## Data pipeline (run from repo root)

```bash
python code/scripts/build_phase1_canonical_base.py        # code/inputs/*.xlsx -> code/intermediates/phase1/*.csv
python code/scripts/generate_readiness_training_rows.py   # -> code/intermediates/training/readiness_training_rows.csv
python code/scripts/build_readiness_training_base.py      # -> code/intermediates/phase1/readiness_training_base.csv
python code/inference_engine/scripts/sync_inputs_from_phase1.py
python code/inference_engine/scripts/train_readiness_model_from_inputs.py   # -> code/outputs/models/
```

Stage notebooks read from `code/intermediates/inference_inputs/` and write their
figures/CSVs directly into `code/outputs/plots/stageN/` and
`code/outputs/reports/stageN/`. Re-run the five commands above after any change to
team files under `code/inputs/` or the KPI config.

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
