# PJTL / Ride YourWay — data flow and control flow

How team files move through the repository into stakeholder outputs. The
folder contract is **`code/inputs/` = .xlsx**, **`code/intermediates/` = CSV / JSON**,
**`code/outputs/` = models + plots + reports**.

## Data flow

```mermaid
flowchart LR
  subgraph inputs["code/inputs/ (PJTL & RYW team, .xlsx only)"]
    X1[Q1 workbook .xlsx]
    X2[Prospective Template .xlsx]
    X3[Prospective Example .xlsx]
  end

  subgraph build["Build scripts (code/scripts/)"]
    B1[build_phase1_canonical_base.py]
    B0[generate_readiness_training_rows.py]
    B2[build_readiness_training_base.py]
    S1[inference_engine/scripts/sync_inputs_from_phase1.py]
  end

  subgraph inter["code/intermediates/"]
    TR[training/readiness_training_rows.csv]
    P1[phase1/*.csv + readiness_training_base.csv]
    INF[inference_inputs/ snapshot + MANIFEST]
  end

  subgraph code["code/inference_engine"]
    NB[Stage 1-3 notebooks]
    TRAIN[train_readiness_model_from_inputs.py]
  end

  subgraph out["code/outputs/ (stakeholders)"]
    OM[models/]
    OR[reports/stage1-3 + phase3_eda]
    OP[plots/stage1-3]
  end

  X1 --> B1
  X2 --> B1
  X3 --> B1
  B1 --> P1
  B0 --> TR
  TR --> B2
  B2 --> P1
  P1 --> S1
  S1 --> INF
  INF --> NB
  INF --> TRAIN
  NB --> OR
  NB --> OP
  TRAIN --> OM
```

**Legend**

| Location | Role |
| --- | --- |
| `code/inputs/` | Team-supplied workbooks (.xlsx only). |
| `code/intermediates/phase1/` | Canonical base tables + audits extracted from `code/inputs/`. |
| `code/intermediates/training/` | Sampled ML training rows (before labeling). |
| `code/intermediates/inference_inputs/` | Flat snapshot of `phase1/` + MANIFEST, used by notebooks and the training script. |
| `code/outputs/models/` | Exported XGBoost model + metadata. The backend Docker image stages these into `/app/inference_models`. |
| `code/outputs/reports/` | Stage-1-3 diagnostics, model card, interpretation notes, phase-3 EDA. |
| `code/outputs/plots/` | Notebook figures. |

## Control flow

```mermaid
flowchart TD
  A[Team drops .xlsx into code/inputs/] --> B[build_phase1_canonical_base.py]
  B --> C[code/intermediates/phase1/*.csv]
  A0[generate_readiness_training_rows.py] --> TR[code/intermediates/training/readiness_training_rows.csv]
  TR --> D[build_readiness_training_base.py]
  D --> C
  C --> E[sync_inputs_from_phase1.py]
  E --> F[code/intermediates/inference_inputs/ + MANIFEST]
  F --> G[Stage 1 notebook -> code/outputs/reports/stage1/ + plots/stage1/]
  G --> H[Stage 2 notebook -> code/outputs/reports/stage2/ + plots/stage2/]
  H --> I[Stage 3 export -> code/outputs/reports/stage3/]
  F --> J[train_readiness_model_from_inputs.py -> code/outputs/models/]
  M[code/config/pjtl_kpis_and_formulas.json] --> B
  M --> D
  M --> N[FastAPI viability engine]
  J --> N
```

**Commands (repo root)**

```bash
python code/scripts/build_phase1_canonical_base.py
python code/scripts/generate_readiness_training_rows.py
python code/scripts/build_readiness_training_base.py
python code/inference_engine/scripts/sync_inputs_from_phase1.py
python code/inference_engine/scripts/train_readiness_model_from_inputs.py
# Optional: re-run the Stage 1-3 notebooks to refresh code/outputs/reports + plots.
```
