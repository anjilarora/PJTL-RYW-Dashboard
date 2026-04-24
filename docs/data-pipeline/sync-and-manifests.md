# Inference-inputs snapshot and manifests

**Script**:
[code/inference_engine/scripts/sync_inputs_from_phase1.py](../../inference_engine/scripts/sync_inputs_from_phase1.py)

**Output directory**: `code/intermediates/inference_inputs/`

## What it does

Freezes the phase-1 canonical base plus the labeled training base under
one directory so that notebooks, the training script, and the sensitivity
harness all look at the same snapshot.

## Files produced

- Copies of every CSV from `code/intermediates (regenerable phase artifacts pruned)/`.
- `readiness_training_base.csv` (copied or symlinked from the training
  base builder's output).
- `MANIFEST.json` - one entry per file in the snapshot with filename,
  size, and SHA-256.
- `MANIFEST.upstream.json` - same format but for the *source* files under
  `code/inputs/` and `code/intermediates (regenerable phase artifacts pruned)/`. This is the
  fingerprint of "what was phase-1 when we snapped".

## Why two manifests

- `MANIFEST.json` tells you "what is inside this directory right now".
  The training script and notebooks check this to validate they did not
  get a partial snapshot.
- `MANIFEST.upstream.json` tells you "what upstream state produced this
  snapshot". A diff of this file between runs answers "did phase-1 change
  and I forgot to re-sync?".

## When to run

Any time:

- `code/intermediates (regenerable phase artifacts pruned)/` changes (after a phase-1 rebuild).
- `readiness_training_base.csv` is rebuilt.
- The xlsx under `code/inputs/` changes.

The convention is to always run the full canonical order from
[overview.md](./overview.md) rather than remembering which step covers
which input.

## Where it is consumed

- [train_readiness_model_from_inputs.py](../../inference_engine/scripts/train_readiness_model_from_inputs.py)
  reads `readiness_training_base.csv` here, not from the training folder.
- [stage1_eda_inference.ipynb](../../inference_engine scripts),
  [stage2_modeling_diagnostics.ipynb](../../inference_engine scripts),
  and [stage3_export_backend_model.ipynb](../../inference_engine scripts)
  read every CSV here.
- [test_readiness_edge_cases.py](../../inference_engine/scripts/test_readiness_edge_cases.py)
  reads the metadata written by the training script whose feature order
  originated from this snapshot.

## Why a snapshot at all

Early in the project the notebooks read directly from `phase1/` and
everyone was getting different artifact versions because someone had
partially re-run `build_phase1_canonical_base.py`. Adding a frozen
snapshot under `inference_inputs/` with content-addressed manifests gave
the notebooks a stable contract.

See [code/intermediates/inference_inputs/README.md](../../intermediates/inference_inputs/README.md)
for the README that ships with the snapshot.
