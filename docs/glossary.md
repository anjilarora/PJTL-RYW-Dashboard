# Glossary

Domain and product terms used throughout the codebase and documentation. If a
term appears in a gate definition, API schema, or dashboard copy, it should be
here with an authoritative definition.

## Kent-Leg
A Kent-Leg is Ride YourWay's **normalized trip unit**. It converts a raw trip
distance (in miles) into a single comparable unit so that wheelchair,
ambulatory, stretcher, and SecureCare trips can be aggregated on a common axis.

**Canonical formula** (from
[code/config/pjtl_kpis_and_formulas.json](../config/pjtl_kpis_and_formulas.json)
`kent_leg` block):

```
Kent-Legs = max(min_kent_legs, ((trip_miles - base_miles) / incremental_miles) + 1)
```

With the shipped constants:

- `base_miles = 8.0`
- `incremental_miles = 23.0`
- `min_kent_legs = 1.0`

Interpretation: every trip counts for at least one Kent-Leg; trips above the
8-mile floor accumulate fractional additional legs in 23-mile increments.

**v2 planning formula** (forward-looking) applies mode multipliers on top so
that heavier acuity (stretcher, SecureCare) contributes more legs per trip
than a plain ambulatory run. The v2 form is used exclusively for
planning/prospective-market math; historical KPIs use the audited v1 form.
See [kpi/assumption-register.md](kpi/assumption-register.md).

## SecureCare
Ride YourWay's highest-acuity service tier (medical escort + secured
transport). Shows up in the mode mix and the `high_acuity_share` feature.

## High-acuity mix (SA / SC)
The share of trips that are Stretcher/Ambulance (SA) or SecureCare (SC). Used
as a readiness signal because high-acuity work carries premium revenue per
Kent-Leg and is harder to displace.

## Readiness gate
One of the **nine binary pass/fail conditions** defined in
[code/config/pjtl_kpis_and_formulas.json](../config/pjtl_kpis_and_formulas.json)
(`readiness_metrics`). Each gate compares a computed feature value to a
threshold using a pass rule (`gte`, `lte`, or `lt`).

| # | Key | Threshold | Rule |
|---|---|---|---|
| 1 | `vehicle_utilization` | 0.95 | `>=` |
| 2 | `billed_utilization` | 1.05 | `>=` |
| 3 | `total_volume_pool` | 1.20 | `>=` |
| 4 | `revenue_per_kent_leg` | 70.0 | `>=` |
| 5 | `high_acuity_share` | 0.05 | `>=` |
| 6 | `non_billable_noshow` | 0.10 | `<` |
| 7 | `road_hours_per_vehicle` | 9.0 | `>=` |
| 8 | `contract_concentration` | 0.20 | `<=` |
| 9 | `cost_per_road_hour` | 50.0 | `<=` |

See [kpi/gate-logic.md](kpi/gate-logic.md) for the full definition.

## North-star metric
The **target operating margin** (25%, from
[code/config/pjtl_kpis_and_formulas.json](../config/pjtl_kpis_and_formulas.json)
`north_star`). Unlike the nine gates, it is not a binary pass/fail; it is the
long-run profitability north star the gates approximate.

## Pass rule
A three-valued enum (`gte`, `lte`, `lt`) that says how a feature value is
compared to its threshold. Implemented in
[code/backend/engine/kpi_config.py](../backend/engine/kpi_config.py)
`passes_gate()`.

## Provisional gate
A gate that **technically passes** under the current data but where the source
formula is still unresolved or uses an assumption-backed denominator. Tier 2
readiness is primarily driven by the number of provisional gates. See
[kpi/tier-policy.md](kpi/tier-policy.md).

## Tier 1 / 2 / 3
- **Tier 1 - Audited**: every input gate has an audited source formula.
- **Tier 2 - Assumption-Backed**: at least one input gate relies on an
  assumption (cost ceiling, Kent-Leg v2 multipliers, program-level
  concentration proxy).
- **Tier 3 - Override**: analyst has manually forced a decision.

See [kpi/tier-policy.md](kpi/tier-policy.md).

## Role (X-Role)
One of `analyst`, `ops`, `admin` from
[code/backend/api/schemas.py](../backend/api/schemas.py) `Role` literal.
Delivered over the `X-Role` HTTP header in demo mode or via the `role` JWT
claim in production. Ordering from least to most privileged:
`analyst` < `ops` < `admin`.

## Ready / Provisional / No-Go
The three possible readiness verdicts the UI displays:

- **Ready**: all nine gates pass and the readiness classifier says Ready with
  probability >= 0.5.
- **Provisional**: at least one gate is provisional or the classifier falls
  in the uncertainty band; launch is not blocked but requires analyst sign-off.
- **No-Go**: one or more strict gates fail; decision is blocked until the
  gap is closed.

See [code/backend/engine/evaluation/readiness_classifier.py](../backend/engine/evaluation/readiness_classifier.py).

## Charter ceiling
The flat $50 per road-hour cost cap used when market-level cost detail is
not yet validated. Appears in the `cost_per_road_hour` gate. The gate passes
**automatically** whenever the ceiling is active because the projected cost
equals the threshold exactly. Its pass should be read as provisional until
regional cost coefficients are available.

## Phase-1 canonical base
The set of clean CSVs produced by
[code/scripts/build_phase1_canonical_base.py](../scripts/build_phase1_canonical_base.py)
from the three intake workbooks. All downstream modeling reads from this
snapshot, not from the raw xlsx files.

## Training base
The CSV produced by
[code/scripts/build_readiness_training_base.py](../scripts/build_readiness_training_base.py)
at `code/intermediates/inference_inputs/readiness_training_base.csv`. Contains
the 9 feature columns plus `label_ready` in `{0, 1}`.

## Inference inputs snapshot
The copy of phase-1 outputs plus the labeled training base, frozen under
`code/intermediates/inference_inputs/`. Generated by
[code/inference_engine/scripts/sync_inputs_from_phase1.py](../inference_engine/scripts/sync_inputs_from_phase1.py).
This directory is what notebooks and the training script read from.

## Flip (as in "1% flip")
A change in the model's decision caused by a small perturbation of a single
feature value across its gate threshold. The sensitivity harness (T1..T6)
enforces that a 1% relative change at any gate flips the classifier output.
See [ml/sensitivity-harness.md](ml/sensitivity-harness.md).

## RYW_REPO_ROOT
Env var honored by
[code/backend/api/repo_root.py](../backend/api/repo_root.py) to let the backend
container find the synthetic `code/config/`, `code/inputs/`, `code/scripts/`
tree staged at `/workspace`. Without this override, the backend walks up from
the application directory looking for the `code/config/` marker.
