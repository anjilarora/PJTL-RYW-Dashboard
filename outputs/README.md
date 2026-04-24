# Outputs (runtime artifacts)

This directory now keeps only runtime-critical outputs.

| Path | Contents |
| --- | --- |
| `models/` | `xgboost_readiness.json` + `xgboost_readiness_metadata.json` consumed by backend inference. |
| `reports/operational_eda/` | CSV artifacts read by operational dashboard API endpoints. |

The large stage-level plots/reports were intentionally removed during cleanup.
Regenerate them from scripts/notebooks only when needed.

Folder contract: `code/inputs/` = `.xlsx`, `code/intermediates/` = CSV/JSON,
`code/outputs/` = runtime model artifacts + selected reports.
