# ADR 0002 - Model artifact location

## Status

Accepted (2026-04-15).

## Context

The XGBoost model needed one authoritative location so the backend
image, the stage notebooks, and the regression harness all point at the
same file. Early drafts spread the model across
`code/inference_engine/models/`, `code/backend/inference_models/`, and
`code/output/` (note the typo), which made "which model is shipped?"
an unanswerable question.

## Decision

1. The **canonical** model directory is
   `code/outputs/models/xgboost_readiness_stage3_v2/` - the stage-3
   notebook's export. This is what the backend Dockerfile `COPY`s to
   `/app/inference_models` and what the `/ready` endpoint validates.
2. The **CI regression** model is
   `code/outputs/models/xgboost_readiness_inputs_v1/` - the training
   script's export. It exists so CI can produce a model without a
   Jupyter kernel.
3. Both directories live under `code/outputs/models/` (not under
   `code/inference_engine/` or `code/backend/`). See ADR 0003.

## Consequences

- One place to look for "what model is running".
- The backend Dockerfile is explicit about which version it ships:
  `COPY code/outputs/models /app/inference_models` plus the
  `RYW_INFERENCE_MODEL_DIR` selection (currently defaults to the
  directory containing both).
- The training script and the notebook must never disagree on feature
  order; the stage-3 notebook validates this and regenerates
  `xgboost_readiness_metadata.json` each run.
- Path strings in metadata are **repo-relative** (see ADR 0003 guard
  rails) to avoid the stage-3 regression where `interpretation_artifact`
  became an absolute filesystem path.

## Alternatives considered

- **Model inside `code/backend/`.** Tightly couples the artifact to the
  service. Rejected because the model is a pipeline output, not a
  backend source file.
- **Model under `code/inference_engine/`.** Mixed with notebooks and
  scripts. Rejected because that directory holds generators, not
  generated artifacts.
- **Separate registry service.** Valuable at scale, unnecessary for an
  in-repo demo where reproducibility matters more than versioning.
