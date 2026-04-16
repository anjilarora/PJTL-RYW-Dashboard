# Outputs (stakeholders)

Final artifacts — the model the backend serves, notebook plots, and summary
reports. These are the canonical write targets for the training script and the
inference-engine notebooks (no separate "publish" step is needed).

| Path | Contents |
| --- | --- |
| `models/` | `xgboost_readiness.json` + `xgboost_readiness_metadata.json` — written by `code/inference_engine/scripts/train_readiness_model_from_inputs.py`. The backend Dockerfile stages these into `/app/inference_models`. |
| `reports/stage1/` | Stage-1 EDA: dtypes, duplicates, missingness rates, correlation matrix, stage-1 model frame. |
| `reports/stage2/` | Stage-2 modeling: threshold sweeps, confusion matrices, feature importance, tree tables, `stage2_summary.json`. |
| `reports/stage3/` | Stage-3 export: `model_card.json`, `stage3_metrics.json`, `error_tradeoff_interpretation.md`. |
| `reports/phase3_eda/` | Phase-3 EDA summary (`eda_summary.json`, `feature_correlation.csv`, `feature_describe.csv`, `threshold_f1_curve.json`). |
| `reports/data_and_control_flow.md` | Pipeline diagram and control flow. |
| `plots/stage1/`, `plots/stage2/`, `plots/stage3/` | PNG figures from the stage notebooks. |
| `plots/*.png` | Cross-stage exploratory figures (correlation, PCA, mode violins). |

Folder contract: `code/inputs/` = `.xlsx`, `code/intermediates/` = CSV / JSON,
`code/outputs/` = models, plots, reports.
