# Training rows generation

**Script**:
[code/scripts/generate_readiness_training_rows.py](../../scripts/generate_readiness_training_rows.py)

**Output**: `code/intermediates/inference_inputs/readiness_training_rows.csv` (regenerable)

## What this script produces

A single CSV carrying one row per synthetic feature vector. Each row has
the nine readiness features plus bookkeeping columns:

- The nine gate features (see [ml/feature-reference.md](../ml/feature-reference.md)).
- `population` - one of `bulk`, `boundary`, `flip`. Lets the training
  base builder sample each group appropriately.
- `flip_partner_id` - when `population == "flip"`, the id of the
  paired row that differs in exactly one gate.
- `seed` - deterministic seed used for the row draw.

## Three populations

1. **Bulk** (~70% of rows).
   Broad draws from distributions fit to the phase-1 daily metrics. Gives
   XGBoost enough interior mass to keep trees from over-fitting the
   boundary.
2. **Boundary** (~20%).
   Rows tightly clustered around each gate threshold (relative +/-1% of
   `T`). Without this, trees learn a very coarse decision surface and the
   "1% flip" property fails.
3. **Flip** (~10%).
   Paired rows differing in exactly one feature, one just above and one
   just below the threshold. Labeled `label_ready` will differ by
   construction. This enforces boundary *sharpness*: if the model labels
   both rows the same, the T1 suite fails and the build fails.

## Why synthetic data

There is no large, labeled, real-market dataset to train on. The project
ships with three workbooks and one worked example. Training a classifier
on those alone would not generalize and would not give the sliders the
sensitivity analysts expect. Synthetic rules-based data:

- Makes the model's decision boundary deterministically match the gate
  rules.
- Lets the test harness verify "1% relative change flips the decision".
- Gives analysts a model that interpolates *smoothly* between gates so
  small improvements in a feature nudge `p(Ready)` upward visibly.

When real labeled markets exist, extend this script to emit a
`population == "real"` population and blend them via sample-weighting.

## How to run

```bash
cd code
python scripts/generate_readiness_training_rows.py
```

Default row counts and the three-population ratio live at the top of the
script as module-level constants; tune them there.

## Determinism

The script seeds every numpy RNG with a per-population integer so reruns
produce byte-identical CSVs. This is the reason the file can sit under
`code/intermediates/` in git without churning on every pipeline run.

## Relation to the training base

The training base builder (next doc) joins these rows with phase-1 summary
stats and *re-labels* each row using the gate rules in
[code/config/pjtl_kpis_and_formulas.json](../../config/pjtl_kpis_and_formulas.json).
This separation (generate -> label) makes it easy to change a threshold
in one place and re-label without regenerating draws.
