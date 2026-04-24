# Inference inputs (metadata-only snapshot)

This folder currently keeps only snapshot metadata:
- `MANIFEST.json`
- `MANIFEST.upstream.json`

Bulk CSVs were removed during repository cleanup. Rebuild/sync them with:
`code/inference_engine/scripts/sync_inputs_from_phase1.py` after regenerating
`code/intermediates (regenerable phase artifacts pruned)/`.
