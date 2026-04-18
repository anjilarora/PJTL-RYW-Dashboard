# Gate logic

The nine readiness gates are defined once in
[code/config/pjtl_kpis_and_formulas.json](../../config/pjtl_kpis_and_formulas.json)
and read by every other component via
[code/backend/engine/kpi_config.py](../../backend/engine/kpi_config.py).

## The nine gates

| # | Key | Display | Threshold | Rule | Symbol |
|---|---|---|---|---|---|
| 1 | `vehicle_utilization` | Vehicle utilization | 0.95 | `gte` | `>=` |
| 2 | `billed_utilization` | Billed utilization | 1.05 | `gte` | `>=` |
| 3 | `total_volume_pool` | Total volume pool | 1.20 | `gte` | `>=` |
| 4 | `revenue_per_kent_leg` | Revenue per Kent-Leg | 70.0 | `gte` | `>=` |
| 5 | `high_acuity_share` | High-acuity trip mix (SA/SC) | 0.05 | `gte` | `>=` |
| 6 | `non_billable_noshow` | Non-billable no-show rate | 0.10 | `lt` | `<` |
| 7 | `road_hours_per_vehicle` | Road hours per vehicle per day | 9.0 | `gte` | `>=` |
| 8 | `contract_concentration` | Contract concentration | 0.20 | `lte` | `<=` |
| 9 | `cost_per_road_hour` | Cost per road hour | 50.0 | `lte` | `<=` |

See [ml/feature-reference.md](../ml/feature-reference.md) for the
business meaning of each gate.

## Pass rule implementation

```python
# code/backend/engine/kpi_config.py
def passes_gate(value: float, threshold: float, pass_rule: str) -> bool:
    if pass_rule == "gte":
        return value >= threshold
    if pass_rule == "lte":
        return value <= threshold
    if pass_rule == "lt":
        return value < threshold
    raise ValueError(f"unknown pass_rule: {pass_rule}")
```

The UI renders the pass rule as a glyph (`>=`, `<=`, `<`) so copy like
`gte 0.95` never escapes to end users. This rendering was a late
polish commit - see [changelog.md](../changelog.md) `Apr 10 10:17:48
EDT` entry.

## How the UI combines them into a verdict

1. For each gate, compute the feature value from the viability report.
2. Apply `passes_gate()` to decide pass/fail.
3. Mark a gate **provisional** when its backing formula has an open
   assumption (see [assumption-register.md](./assumption-register.md)).
4. Count `passing_count`, `failing_count`, `provisional_count`.
5. `engine.evaluation.readiness_classifier.classify_readiness` returns
   one of `Ready`, `Provisional`, `No-Go` based on the counts and the
   XGBoost probability.
6. `engine.evaluation.confidence.derive_confidence_tier` produces the
   Tier 1 / 2 / 3 label.

## Tier logic lives separately

Tier is **not** derived from the gate pass/fail mix alone. It depends
on whether the input formulas themselves are audited. See
[tier-policy.md](./tier-policy.md).

## How to change a threshold

1. Edit the value in
   [code/config/pjtl_kpis_and_formulas.json](../../config/pjtl_kpis_and_formulas.json).
2. Re-run the offline pipeline (training base is re-labeled; model
   re-exports). See [data-pipeline/overview.md](../data-pipeline/overview.md).
3. Re-run `test_readiness_edge_cases.py --strict`. Any T1/T4 miss
   means the new threshold is too close to the slider range edges.
4. Update the corresponding slider min/max in
   [code/frontend/pages/index.vue](../../frontend/pages/index.vue) if
   the new threshold falls outside the existing range.
5. Document the change in [changelog.md](../changelog.md) and add an
   assumption row if the new threshold is still
   assumption-backed.
