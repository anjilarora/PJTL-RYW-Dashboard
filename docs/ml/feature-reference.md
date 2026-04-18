# Feature reference

The readiness classifier takes exactly nine features. They are defined
once in
[code/config/pjtl_kpis_and_formulas.json](../../config/pjtl_kpis_and_formulas.json)
(`readiness_metrics`) and consumed from there by the backend engine, the
training scripts, the sensitivity harness, and the UI. If you change a
threshold, change it in the config file; everything else reads from it.

## Catalog

| # | Key | Display name | Threshold | Rule | Business meaning |
|---|---|---|---|---|---|
| 1 | `vehicle_utilization` | Vehicle utilization | 0.95 | `>=` | Productive vehicle time / available time. Low values mean fleet is idle. |
| 2 | `billed_utilization` | Billed utilization | 1.05 | `>=` | Billed legs / available fleet capacity. >1 indicates revenue density above raw utilization. |
| 3 | `total_volume_pool` | Total volume pool | 1.20 | `>=` | Size of the accessible trip pool relative to the fleet, proxy for demand depth. |
| 4 | `revenue_per_kent_leg` | Revenue per Kent-Leg | 70.0 | `>=` | Dollars of realized revenue per normalized trip unit. |
| 5 | `high_acuity_share` | High-acuity trip mix (SA/SC) | 0.05 | `>=` | Share of trips in stretcher/ambulance or SecureCare - higher acuity = higher unit economics. |
| 6 | `non_billable_noshow` | Non-billable no-show rate | 0.10 | `<` | Share of dispatched trips that do not bill. Keep low. |
| 7 | `road_hours_per_vehicle` | Road hours per vehicle per day | 9.0 | `>=` | Average active road hours per vehicle-day. |
| 8 | `contract_concentration` | Contract concentration | 0.20 | `<=` | Top contract's share of weekly volume. Lower = safer. |
| 9 | `cost_per_road_hour` | Cost per road hour | 50.0 | `<=` | Fully-loaded cost per road hour. Capped at $50 by charter until audited cost data exists. |

## Pass rule semantics

- `gte` -> rendered as `>=`; value passes when `value >= threshold`.
- `lte` -> rendered as `<=`; value passes when `value <= threshold`.
- `lt`  -> rendered as `<`;  value passes when `value < threshold`  (used
  only for `non_billable_noshow`).

Implemented in
[code/backend/engine/kpi_config.py](../../backend/engine/kpi_config.py)
`passes_gate()`.

## Field pedigree

Each feature flows through the pipeline as follows:

1. Extracted/computed by the viability pipeline in
   [engine/pipeline.py](../../backend/engine/pipeline.py) from a
   combination of the Q1 daily metrics and the prospective-market
   intake.
2. Mapped into the inference request payload by
   [api/ml_features.py](../../backend/api/ml_features.py)
   (`report_dict_to_inference_features`).
3. Served to the model via `inference.service.engine.predict(features)`.
4. Returned to the UI in the `/api/v1/viability/evaluate` response under
   `readiness.features`.

## Why exactly these nine

They are the binary gates in the Ride YourWay launch charter. Adding a
tenth feature means extending the KPI config, re-running the full
pipeline, and re-validating the sensitivity harness. Removing one means
weakening the launch criterion.

## North-star metric

The 25% target operating margin lives in the same config under
`north_star` but is **not** a feature of the classifier. It is a
downstream profitability target the UI displays for context.
