# Training base build

**Script**:
[code/scripts/build_readiness_training_base.py](../../scripts/build_readiness_training_base.py)

**Output**:
`code/intermediates/inference_inputs/readiness_training_base.csv`

## Purpose

Join the generated training rows with phase-1 summary statistics, apply
the nine gate rules from
[code/config/pjtl_kpis_and_formulas.json](../../config/pjtl_kpis_and_formulas.json),
and write a single CSV with the nine features, `label_ready in {0,1}`,
and provenance columns.

## Labeling rule

For each row, evaluate each of the nine gates using
`engine.kpi_config.passes_gate(value, threshold, pass_rule)`. If all nine
gates pass, `label_ready = 1`. Otherwise `label_ready = 0`. This is the
definition of "Ready" the model has to learn.

## Output schema

| Column | Description |
|---|---|
| `vehicle_utilization` .. `cost_per_road_hour` | The nine readiness features, in the exact order returned by `engine.kpi_config.feature_order()`. |
| `label_ready` | 0 or 1 per the labeling rule above. |
| `population` | `bulk` / `boundary` / `flip`. Preserved for downstream stratified splits. |
| `gate_pass_mask` | Nine-bit string, one bit per gate, for diagnostics. |
| `source_row_id` | Original id from `readiness_training_rows.csv`. |

## Inputs

- `code/intermediates (regenerable training artifacts pruned)/readiness_training_rows.csv` (from the
  prior script).
- `code/intermediates (regenerable phase artifacts pruned)/*.csv` for any summary stats that the rows
  need (e.g., peer-market revenue-per-Kent-Leg to scale boundary draws).
- `code/config/pjtl_kpis_and_formulas.json` for thresholds and pass rules.

## Provenance

Writes a `training_base_provenance.json` alongside the CSV that records:

- SHAs of `readiness_training_rows.csv` and the KPI config document.
- Row counts split by `label_ready` (sanity check that both classes are
  non-empty - this was the bug that motivated the rebuild).
- Input rows file path as `code/intermediates (regenerable training artifacts pruned)/readiness_training_rows.csv`.
- KPI config path as `code/config/pjtl_kpis_and_formulas.json`.

## Why the split from row generation

Two reasons:

1. Threshold changes (e.g., moving `cost_per_road_hour` from 50 to 48)
   should not require regenerating random draws. Separating generate and
   label makes this a one-file change.
2. The two scripts have very different invariants. Generation is a pure
   draw and should be deterministic across environments. Labeling has to
   load the KPI document, which is a real file-system dependency.
