# Deliverables catalog

> **Related reading**
> - [workbooks/sheet-inventory.md](workbooks/sheet-inventory.md) — data sources.
> - [workbooks/operational-eda.md](workbooks/operational-eda.md) — cited
>   numbers behind every D1..D10 deliverable.
> - Every D1..D10 item is served by a FastAPI endpoint in
>   [`code/backend/api/routes/operational.py`](../backend/api/routes/operational.py)
>   and rendered by a Vue panel in `code/frontend/components/` (filenames
>   mirror each deliverable, e.g. `FleetScorecardPanel.vue`).

Three tables:

1. **Scope deliverables** — the six student deliverables the CEO listed in the
   project scope doc. Status is as of the last commit.
2. **Value-add (D1..D10)** — ranked extras we can ship from the existing
   extracts without new data.
3. **Deferred (pending external data)** — catalogued ideas that require data
   RYW does not have in Q1 2026.

---

## 1. Scope deliverables (from `Ride YourWay × PJTL Project Scope & Key Information.docx` § 6)

| # | Scope deliverable | Shipped surface | Data source | Evidence |
|---|---|---|---|---|
| S1 | Import static market data | Upload workflow on Dashboard, intake-template parsing | `RideYourWay_Prospective_Market_Intake_Template.xlsx` + `Q1 Daily Metrics 2026.xlsx` | [ops/docker.md](ops/docker.md#upload-workflow), [api/upload-workflow.md](api/upload-workflow.md) |
| S2 | Export binary Go / No-Go decision | Dashboard header banner + `/api/v1/inference/predict` | XGBoost model `code/outputs/models/xgboost_readiness_*.json` | [ml/model-card.md](ml/model-card.md), [ml/sensitivity-harness.md](ml/sensitivity-harness.md) |
| S3 | Visualize as dashboard | Full SPA at `code/frontend/` | Backend `/api/v1/*` | [frontend/spa-navigation.md](frontend/spa-navigation.md) |
| S4 | Sensitivity testing | Sliders on Dashboard → Inference tab; T1–T6 harness | `test_readiness_edge_cases.py` | [ml/sensitivity-harness.md](ml/sensitivity-harness.md) |
| S5 | Document assumptions | Assumption register panel; Source & Formula trace | `dashboardData.ts` + KPI config | [kpi/assumption-register.md](kpi/assumption-register.md), [kpi/gate-logic.md](kpi/gate-logic.md) |
| S6 | 9-gate readiness model | Gate Scorecard (carousel + detail tab) | `code/config/pjtl_kpis_and_formulas.json` | [kpi/gate-logic.md](kpi/gate-logic.md) |

All six scope deliverables are shipped. This catalog is the single source of
truth that ties each back to its UI, its backing data, and the doc that
explains it.

---

## 2. Value-add deliverables (D1 … D10)

Ranking criterion: magnitude of operator impact × data completeness × number
of clicks saved on the existing Ops tab. All ten are built from the CSV
aggregates produced by
[`code/inference_engine/scripts/operational_eda.py`](../inference_engine/scripts/operational_eda.py);
none require new data collection.

Shell: the **"Operational deep dive"** tab on `code/frontend/pages/dashboard.vue`
lazy-loads every panel via [`code/frontend/composables/useOperationalData.ts`](../frontend/composables/useOperationalData.ts).
Each panel reuses the shared `RingStat` / `BarStat` / `InfoTip` / `StatusPill`
primitives plus new single-purpose components so we do not introduce a new
component language. All ten are shipped.

| Rank | ID | Deliverable | What it answers | Data source | API | Panel |
|---|---|---|---|---|---|---|
| 1 | D1 | **Regional (fleet) scorecard** | All nine gates per region, side by side. Solves the "which fleet is the problem" question in one glance. | `fleet_gate_scorecard.csv` | `GET /api/v1/dashboard/fleet-scorecard` | [FleetScorecardPanel.vue](../frontend/components/FleetScorecardPanel.vue) |
| 2 | D2 | **Weekly gate trend** | Week 1 → Week 5 sparklines of every gate with WoW deltas. Proves the improvement/regression narrative. | `weekly_gate_trend.csv` | `GET /api/v1/dashboard/weekly-trend` | [WeeklyTrendPanel.vue](../frontend/components/WeeklyTrendPanel.vue) |
| 3 | D3 | **Mode mix & profitability** | Ambulatory / Wheelchair / Stretcher / SecureCare share + Rev/KL + no-show rate. | `mode_profitability.csv` | `GET /api/v1/dashboard/mode-profitability` | [ModeMixPanel.vue](../frontend/components/ModeMixPanel.vue) |
| 4 | D4 | **OTP matrix** | Week × day × region × A-/B-/overall-leg OTP grid with the 90% gate threshold. | `otp_matrix.csv` | `GET /api/v1/dashboard/otp` | [OtpMatrixPanel.vue](../frontend/components/OtpMatrixPanel.vue) |
| 5 | D5 | **Payer concentration early-warning** | Per-payer distance to the 20% cap (volume + revenue). Flags payers over or near the cap. | `payer_concentration.csv` | `GET /api/v1/dashboard/payer-concentration` | [PayerConcentrationPanel.vue](../frontend/components/PayerConcentrationPanel.vue) |
| 6 | D6 | **Hourly demand / idle windows** | 24×7 heat map + idle-cell callout list. Supports redeploy and overtime policy. | `hourly_demand_idle.csv` | `GET /api/v1/dashboard/hourly-demand` | [HourlyDemandPanel.vue](../frontend/components/HourlyDemandPanel.vue) |
| 7 | D7 | **Cancellation-pattern analyzer** | Top reason / mode / day / payer lists + loudest combinations table. | `cancellation_patterns.csv` | `GET /api/v1/dashboard/cancellations` | [CancellationPanel.vue](../frontend/components/CancellationPanel.vue) |
| 8 | D8 | **Revenue / Kent-Leg waterfall by payer** | Which payers lift vs drag the $70 target. Contract renegotiation tool. | `payer_rev_per_kentleg.csv` | `GET /api/v1/dashboard/rev-per-kl` | [RevPerKentlegPanel.vue](../frontend/components/RevPerKentlegPanel.vue) |
| 9 | D9 | **SecureCare vs base-fleet compare** | Side-by-side weekly revenue, cost, margin and a margin sparkline. | `cost_margin_trend.csv` | `GET /api/v1/dashboard/securecare-compare` | [SecureCareComparePanel.vue](../frontend/components/SecureCareComparePanel.vue) |
| 10 | D10 | **Regional cost-per-road-hour estimate** | Estimated cost per region using published fleet counts. Explicitly flagged "estimate" until RYW breaks cost down. | `regional_cost_estimate.csv` | `GET /api/v1/dashboard/cost-regional` | [RegionalCostPanel.vue](../frontend/components/RegionalCostPanel.vue) |

All ten panels are served by [`code/backend/api/routes/operational.py`](../backend/api/routes/operational.py)
and covered by `code/backend/tests/test_operational.py`.

### How ranks were chosen

- **Impact** — does the operator act differently after seeing it?
  (e.g. D1 changes where Mike allocates a dispatcher; D10 only changes how
  we caveat cost.)
- **Data completeness** — how confident are we in the numbers? D1..D8 use
  first-party data; D9 and D10 rely on derived totals.
- **Click-count saved** — D1 replaces a 3-sheet cross-reference with one
  card; D10 replaces nothing (pure new visibility).

---

## 3. Deferred (pending external data)

Catalogued so product + data teams can prioritise what to gather next. Each
entry names the exact data source that unblocks it.

| # | Deliverable | Blocker | Unblock source |
|---|---|---|---|
| X1 | **Per-region cost-per-road-hour (real, not estimate)** | Per-region driver wage, overhead, gas split not in Q1 data | Zach / CFO spreadsheet of regional GL allocations |
| X2 | **Population-65+ demand forecast** | No demographic feature in the Q1 workbook | Census ACS 5-year tables by county |
| X3 | **Competitor presence map** | No competitor field anywhere in the data pack | Market survey or NEMT provider registry |
| X4 | **Facility density layer** | Only zones in the trip log; no facility catalog | Medicare-certified facility CSV (CMS) |
| X5 | **Deadhead distance true-up** | Trip log contains PU/DO zone only; no vehicle start position | GPS telemetry (missing from Q1 extract) |
| X6 | **Weather / seasonality overlay** | No weather column | NOAA daily weather by zone |
| X7 | **Vehicle → region mapping** | `Vehicle Breakdown` has vehicle IDs only | RYW dispatch roster |
| X8 | **Driver productivity benchmark** | `Driver Active Time` lacks fleet anchor | Driver→fleet roster |
| X9 | **Contract margin at contract level** | Aggregate only; individual contract P&L missing | Accounting extract per payer |
| X10 | **Route-level profitability** | No route/trip-chain identifier in trip log | Dispatch sequence export |
| X11 | **Market viability calibration on real markets** | Q1 has 3 live markets (GR, Lansing, BC) + 1 skeleton (Detroit); intake template is a prospective-market format | First 2–3 intake submissions from non-MI markets |
| X12 | **OTP Week 5 completeness** | Spreadsheet block under-filled (see [operational-eda.md § 5](workbooks/operational-eda.md#5-otp-matrix)) | RYW refresh of `OTP` sheet |

Deferred items surface as `FeatureGap` entries in the dashboard audit tab
once we add them; today they live only in this doc and the EDA narrative.

---

## Delivery order (as shipped)

All ten deliverables shipped in a single PR. The backend shares
`code/backend/engine/operational_service.py`, the frontend uses one composable
(`code/frontend/composables/useOperationalData.ts`) that lazy-loads per-panel
data when the **Operational deep dive** tab activates, and every artifact is
regenerated by running `python code/inference_engine/scripts/operational_eda.py`
or the companion notebook.
