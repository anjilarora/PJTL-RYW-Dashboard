# Assumption register

The open assumptions behind the readiness computation. The UI renders
them on the dashboard in the "Open assumptions" section so analysts
can see which gates are still mechanical approximations. Source of
truth: the `assumptions` array in
[code/frontend/server/utils/dashboardData.ts](../../frontend/server/utils/dashboardData.ts).

## Why an assumption register

Launch readiness is only as trustworthy as the formulas underneath it.
Some gates rely on proxies because the audited data stream is not yet
available. Capturing those proxies in one place means:

- Reviewers know what to challenge.
- The tier policy downgrades confidence automatically when an
  assumption is active.
- Ops has a clear backlog of "replace with audited coefficient" items.

## The four open assumptions

### 1. Fleet plan
- **Source**: `market.fleet` x `market.operating_days_per_week`
- The operating plan assumed for the market: how many vehicles and
  how many active days per week we size the fleet for. Used as the
  denominator for **vehicle utilization**, **road-hours per
  vehicle-day**, and **billed utilization** (gates 1, 7, 2).
- Closes when: the prospective-market intake is required to carry the
  operator-confirmed fleet size and cadence.

### 2. Kent-Leg conversion (v2 planning formula)
- **Source**: `kent_leg_planning_v2` x `mode_multipliers`
- A Kent-Leg is the normalized trip unit so we can compare
  wheelchair, ambulatory, stretcher, and SecureCare work on the same
  axis. The **v2 planning formula** is the forward-looking version
  currently in place: each trip is multiplied by a mode-specific
  weight (stretcher and SecureCare carry heavier multipliers than a
  standard ambulatory run) and summed into a weekly Kent-Leg total.
- Rationale for v2: the v1 constants that finance shipped did not
  separate acuity. Until the official Kent-Leg definition is locked,
  v2 is used for *planning* only; historical KPIs use the audited v1
  form.
- Affects **revenue per Kent-Leg** (gate 4) and **total volume pool**
  (gate 3).
- Closes when: finance publishes the audited v2 or re-issues a v1
  that covers acuity.

### 3. Cost basis
- **Source**: `charter.cost_per_road_hour_ceiling`
- Projected hourly cost is pinned to the **$50 charter ceiling**
  until regional cost detail (driver wage, fuel, overhead, operating)
  can be validated for the corridor. Because cost is capped rather
  than measured, the **cost-per-road-hour gate clears automatically**;
  its pass should be read as **provisional** until the ceiling is
  replaced by validated coefficients.
- Closes when: market-level driver, fuel, overhead, and operating
  costs are available.

### 4. Concentration proxy
- **Source**: `intake.programs[].weekly_volume_share`
- The launch charter caps concentration **by contract**. The example
  workbook is **program-keyed** (one intake row per program, not per
  contract), so we report the top program's share of weekly volume as
  a **proxy** for contract concentration until contract-level keys
  exist.
- Affects **contract concentration** (gate 8).
- Closes when: the intake template carries a contract_id column and
  the extractor joins programs to contracts.

## Kent-Leg planning v2 formula explained

The audited v1 from
[code/config/pjtl_kpis_and_formulas.json](../../config/pjtl_kpis_and_formulas.json)
is:

```
kent_legs_v1 = max(1.0, ((trip_miles - 8.0) / 23.0) + 1)
```

v2 layers **mode multipliers** on top:

```
kent_legs_v2(trip) =
    kent_legs_v1(trip.miles) * mode_multiplier[trip.mode]
```

with approximate multipliers (exact numbers live in dashboardData /
planning spreadsheets; the config-shipped form is still audited-v1):

| Mode | Multiplier (planning v2) |
|---|---|
| Ambulatory | 1.00 |
| Wheelchair | 1.05 |
| Stretcher | 1.40 |
| SecureCare | 1.75 |

v2 is only applied in **planning** paths. Historical reporting (the Q1
daily metrics feed) uses v1 exclusively so the two time series do not
drift incompatibly.

## How assumptions surface in the UI

- Each row in `assumptions` becomes a card in the dashboard's "Open
  assumptions" panel.
- Matching gates are badged **Provisional** even when the numeric
  comparison passes.
- The tier derivation in
  [engine/evaluation/confidence.py](../../backend/engine/evaluation/confidence.py)
  downgrades to Tier 2 when at least one assumption is active.

## How to retire an assumption

1. Remove the entry from `assumptions` in `dashboardData.ts`.
2. If the change affects a gate formula, update
   [code/config/pjtl_kpis_and_formulas.json](../../config/pjtl_kpis_and_formulas.json)
   and re-run the offline pipeline.
3. Update copy in [kpi/tier-policy.md](./tier-policy.md) and
   [kpi/gate-logic.md](./gate-logic.md).
4. Add a changelog entry noting which gate transitioned from
   provisional to audited.
