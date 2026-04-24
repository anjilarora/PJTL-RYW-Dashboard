# Data pipeline overview

End-to-end path from analyst-edited xlsx to a served XGBoost model and the
UI reports.

## Flow

```mermaid
flowchart TD
  A[code/inputs/<br/>*.xlsx]:::inputs
  B1[build_phase1_canonical_base.py]
  B2[generate_readiness_training_rows.py]
  C1[code/intermediates/<br/>phase-1 metadata + snapshot manifests]:::inter
  C2[code/intermediates/inference_inputs/<br/>readiness_training_rows.csv (regenerable)]:::inter
  D[build_readiness_training_base.py]
  E[code/intermediates/inference_inputs/<br/>readiness_training_base.csv]:::inter
  F[sync_inputs_from_phase1.py]
  G[code/intermediates/inference_inputs/<br/>snapshot + MANIFEST.json]:::inter
  H[train_readiness_model_from_inputs.py]
  I[code/outputs/models/xgboost_readiness_inputs_v1]:::out
  J[stage1_eda_inference.ipynb]
  K[stage2_modeling_diagnostics.ipynb]
  L[stage3_export_backend_model.ipynb]
  M1[code/outputs/reports/operational_eda]:::out
  M2[code/outputs/reports/operational_eda]:::out
  M3[code/outputs/reports/operational_eda]:::out
  M4[regenerable notebooks/plots (not tracked)]:::out
  N[code/outputs/models/xgboost_readiness_stage3_v2]:::out
  O[backend /app/inference_models<br/>via Dockerfile COPY]

  A --> B1 --> C1
  A --> B2 --> C2
  C1 --> D
  C2 --> D --> E
  C1 --> F --> G
  E --> H
  G --> H --> I
  G --> J --> M1
  G --> K --> M2
  M1 --> K
  G --> L --> M3
  M1 --> L
  M2 --> L
  L --> N
  J --> M4
  K --> M4
  L --> M4
  I --> O
  N --> O

  classDef inputs fill:#eef7ff,stroke:#1456a8,stroke-width:1px;
  classDef inter fill:#fdf6e3,stroke:#a07a00,stroke-width:1px;
  classDef out fill:#e9f6ee,stroke:#1f7a3a,stroke-width:1px;
```

## Canonical run order

Run from `code/` with the project venv active.

```bash
python scripts/build_phase1_canonical_base.py
python scripts/generate_readiness_training_rows.py
python scripts/build_readiness_training_base.py
python inference_engine/scripts/sync_inputs_from_phase1.py
python inference_engine/scripts/train_readiness_model_from_inputs.py
jupyter nbconvert --to notebook --execute inference_engine scripts
jupyter nbconvert --to notebook --execute inference_engine scripts
jupyter nbconvert --to notebook --execute inference_engine scripts
```

After stage-3 runs, the **model served by the backend** is
`code/outputs/models/xgboost_readiness_stage3_v2` (the notebook's exported
artifact), not the intermediate produced by the script in step 5. The
script's output is kept for continuous-integration / repro-check purposes;
the notebook's output is what ships.

## Verifying a clean run

- No absolute paths anywhere under `code/outputs/` or
  `code/intermediates/`. Grep for `/Users/` or `/home/` and expect zero
  hits.
- `code/intermediates/inference_inputs/MANIFEST.json` should only reference
  files that currently exist in `code/intermediates/inference_inputs/` (repo-relative).
- `code/outputs/reports/operational_eda/manifest.json` should remain
  repo-relative and never include absolute host paths.
- `code/outputs/models/xgboost_readiness_stage3_v2/xgboost_readiness_metadata.json`
  should carry `training_data.path: "code/intermediates/inference_inputs/readiness_training_base.csv"`.

## When the pipeline fails

| Symptom | Usual cause | Fix |
|---|---|---|
| `FileNotFoundError: code/inputs/Q1 Daily Metrics 2026.xlsx` | Analyst removed the workbook | Restore from the deliverables bundle or the last known good commit. |
| Stage report references `/Users/...` paths | A notebook/script wrote host-absolute paths into a report artifact | Re-run with repo-relative outputs and normalize paths before committing artifacts. |
| Backend `/ready` returns `ready=false` after `docker compose up` | Model directory is empty or the model metadata feature order does not match `InferenceRequest` | Re-run steps 5 and 8, then `docker compose build backend`. |
| Training script crashes on join | Phase-1 snapshot is stale - the `MANIFEST.upstream.json` hash differs from the live `phase1/` | Re-run `sync_inputs_from_phase1.py` to refresh. |

## Why this shape

- The three-layer contract (`inputs/` -> `intermediates/` -> `outputs/`) was
  chosen after a session where generated CSVs had drifted into
  `inference_engine/inputs/` and were edited by hand. Separating human
  inputs (xlsx) from generated intermediates (csv/json) eliminates the
  "who touched this last" class of bug.
- The notebook export is intentionally authoritative for the shipped model
  so that the committed stage-3 report and the binary match exactly. The
  script stays because CI needs a non-notebook way to produce a model for
  regression tests.
- Manifests exist so `diff` can tell you whether the inference_inputs
  snapshot you are looking at matches the current phase-1 output. Without
  them, the question "did someone re-run phase-1 and forget to re-sync?"
  was non-trivial to answer.
