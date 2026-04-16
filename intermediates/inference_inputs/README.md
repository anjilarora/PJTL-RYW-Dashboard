# Inference inputs (intermediate snapshot)

Flat copies of **`code/intermediates/phase1/`** CSVs with `MANIFEST.json` /
`MANIFEST.upstream.json` for notebook + training consumption. Produced by
`code/inference_engine/scripts/sync_inputs_from_phase1.py`.

Do not edit files here by hand; re-run the sync script after rebuilding
`code/intermediates/phase1/`.

The training script (`code/inference_engine/scripts/train_readiness_model_from_inputs.py`)
reads `readiness_training_base.csv` from this directory and writes the final
model artifacts to `code/outputs/models/`.
