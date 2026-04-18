# Training

The readiness classifier is an XGBoost binary classifier. Training is
deterministic given the snapshotted `readiness_training_base.csv`.

## Script

[code/inference_engine/scripts/train_readiness_model_from_inputs.py](../../inference_engine/scripts/train_readiness_model_from_inputs.py)

## Inputs

- `code/intermediates/inference_inputs/readiness_training_base.csv` - the
  labeled training base.
- `code/config/pjtl_kpis_and_formulas.json` - to verify the feature order
  matches the gate catalog.

## Outputs

Directory: `code/outputs/models/xgboost_readiness_inputs_v1/`

Files inside:

- `xgboost_readiness_model.joblib` - pickled `XGBClassifier` (with
  post-hoc calibration wrapper).
- `xgboost_readiness_metadata.json`:
  ```json
  {
    "version": "xgboost_readiness_inputs_v1",
    "trained_at": "2026-04-10T...",
    "feature_order": ["vehicle_utilization", ...],
    "decision_threshold": 0.5,
    "training_data": {
      "path": "code/intermediates/inference_inputs/readiness_training_base.csv",
      "sha256": "..."
    },
    "metrics": {"accuracy": ..., "auc": ..., "brier": ...}
  }
  ```
- Feature importance JSON for the UI to render the explain panel.

## Hyperparameters

Tuned empirically against the sensitivity harness. Current values:

| Param | Value | Why |
|---|---|---|
| `n_estimators` | 400 | Enough depth to capture all nine interactions. |
| `max_depth` | 6 | Shallow enough to keep the decision boundary tight around the thresholds. |
| `learning_rate` | 0.05 | Lower rate + more estimators -> smoother prob surface. |
| `subsample` | 0.8 | Regularize. |
| `colsample_bytree` | 0.9 | Keep most features per tree so every gate can participate. |
| `min_child_weight` | 1 | Boundary-dense rows are allowed to matter. |
| `reg_lambda` | 1.0 | Default L2. |
| `eval_metric` | `logloss` | Calibrated probabilities matter more than accuracy. |

Any change to these values should be accompanied by a `test_readiness_edge_cases.py`
pass with `strict=True`.

## Calibration

After training, we apply sigmoid (Platt-scale) calibration on a held-out
20% split so that `p(Ready)` is interpretable as a probability. This is
why the UI's probability bar feels monotonic when a slider moves.

## How to run

```bash
cd code
python inference_engine/scripts/train_readiness_model_from_inputs.py
```

Exit code is 0 on success; on a T1..T6 harness failure the script exits
non-zero and prints the failing suite.

## Migration path to real data

When real labeled markets are available:

1. Extend `generate_readiness_training_rows.py` with a `population="real"`
   branch.
2. Stream them into `readiness_training_base.csv` with the same
   labeling via `passes_gate`.
3. Sample-weight the real rows higher than synthetic. XGBoost's
   `sample_weight` parameter is the obvious hook.
4. Keep the synthetic boundary/flip rows so the "1% flip" guarantee does
   not regress.

## Relation to the stage-3 notebook

After this script writes `xgboost_readiness_inputs_v1/`, the stage-3
notebook re-trains and exports `xgboost_readiness_stage3_v2/`. The
notebook version is what the Docker image `COPY`s into
`/app/inference_models`. The script-produced artifact stays in the repo
for CI regression tests and so that the training step is runnable
without a Jupyter kernel.
