# Intermediates (generated)

CSV / JSON derivations between team `code/inputs/*.xlsx` and stakeholder `code/outputs/`.
Safe to delete and regenerate with the build scripts in `code/scripts/`.

| Path | Contents |
| --- | --- |
| `phase1/` | Canonical CSV tables + audits extracted from `code/inputs/*.xlsx` by `build_phase1_canonical_base.py`, plus `readiness_training_base.csv` from `build_readiness_training_base.py`. |
| `training/` | ML training feature CSVs. `readiness_training_rows.csv` is emitted by `generate_readiness_training_rows.py` and consumed by `build_readiness_training_base.py`. |
| `inference_inputs/` | Snapshot of `phase1/` (plus `MANIFEST.json` / `MANIFEST.upstream.json`) used by the inference-engine notebooks and the training script. Synced by `code/inference_engine/scripts/sync_inputs_from_phase1.py`. |

Folder contract: `code/inputs/` = `.xlsx`, `code/intermediates/` = CSV / JSON,
`code/outputs/` = final model + plots + reports.
