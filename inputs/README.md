# Inputs (PJTL / RYW team)

Source workbooks from the project team. **`.xlsx` only.** Do not commit generated
CSVs here — those live under `code/intermediates/` after the pipeline runs.

| File | Role |
| --- | --- |
| `Q1 Daily Metrics 2026.xlsx` | Historical operational metrics; the Phase-1 extractor reads named sheets here. |
| `RideYourWay_Prospective_Market_Intake_Template.xlsx` | Prospective intake template. |
| `RideYourWay_Prospective_Market_Intake_Example.xlsx` | Filled prospective example. |

## Why `.xlsx` and not `.csv`

The extractor reads **named sheets** (Contract Volume, Mode Breakdown, Weekly
Margin, SecureCare Profit, etc.) directly from the workbook; a single flat CSV
cannot carry that multi-sheet structure. Use the template above as the shape
contract.

## Pipeline

From the repository root:

```bash
python code/scripts/build_phase1_canonical_base.py       # xlsx  -> code/intermediates/phase1/*.csv
python code/scripts/generate_readiness_training_rows.py  # -> code/intermediates/training/readiness_training_rows.csv
python code/scripts/build_readiness_training_base.py     # -> code/intermediates/phase1/readiness_training_base.csv
python code/inference_engine/scripts/sync_inputs_from_phase1.py
python code/inference_engine/scripts/train_readiness_model_from_inputs.py  # -> code/outputs/models/
```

Folder contract: `code/inputs/` = `.xlsx`, `code/intermediates/` = CSV / JSON derivations,
`code/outputs/` = models, plots, reports.
