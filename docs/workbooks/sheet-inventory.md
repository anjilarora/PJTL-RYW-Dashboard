# Workbook sheet inventory and deliverable mapping

This document enumerates every sheet in every `.xlsx` file shipped with the
repo, explains what each sheet holds, and maps it back to the project
deliverables captured in the RYW scope doc, internal data-comments doc, and
the weekly sync meeting logs.

> **Related reading**
> - [operational-eda.md](operational-eda.md) — the 10-section operational EDA
>   that consumes every sheet inventoried here.
> - [../deliverables.md](../deliverables.md) — the catalog of in-scope
>   deliverables, the ten value-add deliverables (D1..D10) built from those
>   sheets, and what remains deferred pending additional data.

Three files live under [code/inputs/](../../inputs/) and are consumed by the
offline pipeline and the upload API. A fourth live workbook lives in the
meetings folder and tracks project schedule only; it is not read by the app.

## Inventory at a glance

| Workbook | Role | Sheet count | Visible / Hidden |
|---|---|---|---|
| [Q1 Daily Metrics 2026.xlsx](../../inputs/Q1%20Daily%20Metrics%202026.xlsx) | RYW live-market operating data for Q1 2026 (Dec 29 2025 – Jan 31 2026). Single source for the nine readiness gates. | 12 | 10 visible, 2 hidden |
| [RideYourWay_Prospective_Market_Intake_Template.xlsx](../../inputs/RideYourWay_Prospective_Market_Intake_Template.xlsx) | Blank intake the CEO hands to prospects (hospitals, SNFs, brokers, health plans, community orgs). | 5 | 5 visible |
| [RideYourWay_Prospective_Market_Intake_Example.xlsx](../../inputs/RideYourWay_Prospective_Market_Intake_Example.xlsx) | Fully filled-out intake for "Example Medical Center". Used as the default demo payload and as a shape contract. | 5 | 5 visible |
| `PJTL Internal Meetings/Copy of RYW Gantt Chart W26.xlsx` | Project timeline / EOS rocks tracker for the student team. Not a data input. | 2 | 2 visible |

---

## 1. `Q1 Daily Metrics 2026.xlsx` — live-market operating data

**Provenance.** Authored by Zach (RYW Chief Data Officer). Covers Q1 2026
operating data for the three existing service areas: Grand Rapids (21
vehicles), Lansing (4 vehicles), Battle Creek (5 vehicles). Internal Data
Comments doc confirms Battle Creek is the most positive on 24h cancellation /
OTP / schedule efficiency; Grand Rapids has the most total rides but biggest
broker dependency.

**Used by.** [code/scripts/build_phase1_canonical_base.py](../../scripts/build_phase1_canonical_base.py)
extracts this workbook into the canonical CSV set under
`code/intermediates/phase1/`. The nine-gate scorecard and every dashboard
panel trace back to these extracts.

### Sheet 1 — `Total Performance` (visible, 135 × 44)

Quarter-level and weekly rollups for the entire fleet: Billable NS, Billed
Usage, Non-Billable NS, OTP, Vehicle Usage, Scheduled Usage, Target Capacity,
SKL, KL Multiple. Presents targets next to actuals (e.g. target `85% <` for
Billed Usage, `90% <` OTP, `85% <` Vehicle Usage), so it is the cleanest
snapshot of where RYW is vs its own thresholds.

**Maps to deliverables**
- Feeds Gate #1 (vehicle utilization ≥ 95 %), Gate #2 (billed utilization
  ≥ 105 %), Gate #6 (non-billable no-shows ≤ 10 %), Gate #7 (road time ≥ 9 h).
- Anchors the "weekly operating snapshot" card in the dashboard. The
  historical baseline shown in `KpiSnapshotPanel` and the sensitivity
  `dashboardData.ts` source strings are all derived from this sheet.
- Mirrors the "Design and Implement a Market Readiness Dashboard" Smart Goal
  from the 1/19 internal meeting (vehicle utilization, billed utilization,
  OTP, NS).

### Sheet 2 — `Regional Performance` (visible, 136 × 99)

Same schema as `Total Performance` but split into three side-by-side blocks
for Grand Rapids, Lansing, and Battle Creek. Lets you see that Battle Creek
has lower total volume but cleaner OTP / cancellation.

**Maps to deliverables**
- Powers the "regional context" strip and tier narrative referenced in
  `docs/kpi/tier-policy.md`. Tier 1 (audited gates) is what this sheet can
  evidence directly per region.
- Background for the meeting-log observation: "Grand Rapids biggest issue in
  terms of profitability is broker dependency" and "Battle creek having low
  broker dependency but less density".
- Input to the Module 3 (Capacity & Scheduling) deliverable in the
  design-doc: per-region utilization baselines.

### Sheet 3 — `Mode Breakdown` (visible, 17 961 × 25)

Pivot view: percent and Kent-Leg totals by day of week × order mode
(Ambulatory / Wheelchair / Stretcher) × order-status reason (Turned Down,
Unable to Accommodate, Confirmation Cancel, Same-Day Cancel, No Show, Billed
no show, Completed). Also contains "Revenue By Mode" cross-tab.

**Maps to deliverables**
- Supplies the numerator for Gate #5 (higher-acuity trip mix ≥ 5 %) via the
  Stretcher and SecureCare rows.
- Feeds the Kent-Leg conversion that the scope doc pins down:
  `kent_legs = (miles − 8) / 23 + 1`. The Internal Data Comments doc
  explicitly states "The Kent Legs are converted the same. This can also be
  found in the Mode Breakdown tab."
- Drives the Intake Summary's "class breakdown" panel and the per-mode
  assumptions surfaced in the Sensitivity Scenario panel.

### Sheet 4 — `OTP` (visible, 281 × 37)

On-Time Performance by location × day-of-week, split into A Leg (to
appointment) and B Leg (return). The Internal Data Comments doc clarifies OTP
only counts getting the passenger to the appointment on time; patient
lateness at pickup is *not* excluded.

**Maps to deliverables**
- Although OTP is not one of the nine go/no-go gates, it is one of the
  "quality gates" Hayden flagged at the 1/19 internal meeting and is used to
  weight the tier narrative and the "provisional" status on gates adjacent to
  schedule reliability.
- Feeds the "Why this matters" copy inside the GateDetailPanel for Gate #1
  and Gate #7 (road time / utilization both degrade when OTP drops).

### Sheet 5 — `Contract Volume` (visible, 17 929 × 39)

Row-level trip log: `Payer ID`, PU Zone, DO Zone, Order Mileage, Order Mode,
Order Status, Reason, Order Price, Date Of Service, Pick Up Time, Day, Week,
Offset, Over-under, Mileage Kent Legs, Kent Legs.

This is the **ground truth transactional log** that every aggregate rolls up
from. Every other sheet in the workbook can be reconstructed from it.

**Maps to deliverables**
- Backs Gate #8 (contract concentration ≤ 20 %). The per-payer payer-ID
  grouping is exactly what gets aggregated to compute concentration.
- Source for the Module 1 (Demand) deliverable described in
  `PJTL Design /Detailed Map.docx`: trip density by hour / day / zone / mode.
- Source for the Module 2 (Contract Business Model) deliverable: payer rules,
  billable-no-show classification, broker percentage.
- Feeds every "Source & Formula Trace" panel entry that cites the trip log.

### Sheet 6 — `Heat Map` (visible, 579 × 80)

Demand intensity grid: Day × Hour for total rides, Ride Pool, Available
Capacity, Kent-Leg multiplier (1.3). Includes a "will call" bucket
(B-leg-less-appointments-with-unknown-end). The first cell `Kent Leg
multipler = 1.3` is the internal-volume-pool inflation factor used to size
overbooking.

**Maps to deliverables**
- Direct input into the Module 3 (Capacity & Scheduling) deliverable:
  scheduler uses hourly density to size vehicles per region.
- Background for Gate #3 (total volume pool ≥ 120 %): the heat-map density
  × overbooking multiplier yields the volume-pool calculation.
- Provides the shape rationale for the "schedule efficiency" critique in the
  Internal Data Comments doc.

### Sheet 7 — `Revenue by Payer` (visible, 17 929 × 65)

Same transactional grain as `Contract Volume` but with extended revenue
columns (Order Price pivoted by payer) so you can compute revenue by payer,
revenue by mode, and blended revenue / Kent-Leg.

**Maps to deliverables**
- Primary feed for Gate #4 (revenue / Kent-Leg ≥ $70). Historical benchmark
  of $70 per Kent-Leg is the threshold every UI surface points back to.
- Secondary feed for Gate #8 (concentration on *revenue* side).
- Powers the "Margin Waterfall" and "Intake Summary" dashboard cards once
  the intake workbook is blended with RYW's historical rates.

### Sheet 8 — `Weekly Margin` (visible, 155 × 32)

The cost model. Day × week breakdown of Total Revenue, Total Cost, Profit
Margin %, $ Profit, plus a Cost subsection with Fixed Overhead Cost (the
Internal Data Comments doc confirms: "That is located in the Weekly Margin
tab!").

**Maps to deliverables**
- Feeds Gate #9 (cost per road hour ≤ $50). The current benchmark of $49.50
  during a 23 % margin week referenced in the scope doc comes from this
  sheet.
- Powers the Margin Waterfall panel (revenue, fixed cost, variable cost,
  operating margin). The "charter ceiling of $50 per road hour" copy on the
  dashboard pulls its upper bound from here.
- Primary evidence for the 25 % operating margin target that frames the
  entire readiness decision.

### Sheet 9 — `Corewell Metrics` (**hidden**, 71 × 53)

Pilot-program scaffolding: Total Rides Requested, Total Rides Completed,
Rides Unfulfilled, Percent Complete, by day. Rows are zeroed out — the
pilot has not yet run. Left in the workbook so the cell addresses survive
when the pilot goes live.

**Maps to deliverables**
- Future home of evidence for Corewell-specific concentration checks and the
  pilot's own weekly snapshot.
- The pipeline deliberately **skips this sheet** (it's hidden and empty).
  Documenting it here so future contributors know not to wire it into the
  gate calculator prematurely.

### Sheet 10 — `Vehicle Breakdown` (visible, 2 615 × 67)

Vehicle-level activity log: per-vehicle active time, road hours, driver data.
The Design Doc's Module 4 (Cost) notes "Tab: Vehicle Breakdown — ASK ABOUT
THE DRIVER DATA: ROAD TIME vs ACTIVE TIME". Zach confirmed driver wages live
alongside here.

**Maps to deliverables**
- Primary feed for Gate #7 (road time ≥ 9 h per vehicle per day).
- Supplies the raw driver hours that, multiplied by driver-wage and fuel
  coefficients in the Design Doc, yield Gate #9 (cost per road hour).
- Source for the "deadhead" and "42 % loaded mileage" assumption sub-bullets
  in the Module 3 design.

### Sheet 11 — `SecureCare Profit` (visible, 155 × 35)

Dedicated margin tab for SecureCare (behavioral-health transport). Different
vehicle fleet (2 vehicles: 1 Grand Rapids, 1 Battle Creek), different driver
wages, demand-on-call (ED-triggered). Kept separate so the main Weekly
Margin numbers are not distorted.

**Maps to deliverables**
- Anchors the "higher-acuity lift" story the scope doc asks for: `5%+ mix,
  $200+ avg revenue per trip`. Gate #5 reads mode share from Mode Breakdown
  but reads revenue/cost specifics from this sheet.
- Evidence for "Identify key risks" deliverable: SecureCare is structurally
  low-volume and high-variance, so it is called out as a fragility driver in
  the Risk Mitigation panel.

### Sheet 12 — `Sheet2` (**hidden**, 1 × 1)

Empty placeholder sheet. Not used.

**Maps to deliverables** — none.

---

## 2. `RideYourWay_Prospective_Market_Intake_Template.xlsx` — the blank intake

**Provenance.** Authored jointly by the PJTL team and Tom (CEO). Directly
addresses the 1/19 Smart Goal: "Create a Market Viability Spreadsheet for
Data Input — Develop a standardized spreadsheet that can be used by
prospective contracts and facilities to input data into the master system."

### Sheet 1 — `Start Here` (visible)

Cover sheet that briefly describes the workbook, tells the user to fill only
the blue cells on `Organization Intake`, to add one row per trip pattern on
`Trip Demand Input`, to use average weekly demand where historical data is
missing, and to leave gray formula cells untouched.

**Maps to deliverables**
- The "clear, minimal backend visibility" requirement in
  `PJTL Design /PJTL Design Doc.docx`: "Output clear and non technical,
  minimal backend visibility".
- The onboarding UX described in [code/docs/frontend/upload-ux.md](../frontend/upload-ux.md).

### Sheet 2 — `Organization Intake` (visible)

One-submission organization profile. Columns: Submission ID, Organization
name, Organization Type (Hospital / SNF / Health Plan / Broker / Community /
Behavioral Health / Other), Facility / program name, Primary service area,
Primary city & state, Primary contact, Email, Phone, Data period start,
Data period end, Contract / payer name, Payer type, Expected go-live.

**Maps to deliverables**
- Module 2 (Contract Business Model) input. Every downstream billable-no-show
  rule branches on `Organization Type` + `Payer type`.
- Gate #8 (contract concentration): the Submission ID uniquely identifies
  the prospective contract under evaluation.

### Sheet 3 — `Trip Demand Input` (visible)

One row per trip pattern / service line / program. 22 columns including:
Row ID, Facility Name, Contract / Program, Source Type, Volume Class
(Quality vs Filler), Service Category (Discharge, Recurring Appointment,
Dialysis, Facility Transfer, Behavioral Health, Community Program, Other),
Trip Mode (Ambulatory, Wheelchair, Stretcher Alternative, SecureCare, Other),
Higher-Acuity? (Yes/No), Pickup Zone / ZIP, Dropoff Zone / ZIP, Avg One-Way
Miles, Completed Trips / Week, Billable No-Shows / Week, Non-Billable
No-Shows / Week, Revenue / trip, plus metadata.

**Maps to deliverables**
- This is the principal payload the readiness engine runs inference on. The
  nine-gate decision logic transforms these rows into the gate vector that
  XGBoost scores.
- Gate #5 mix, Gate #4 revenue-per-Kent-Leg, Gate #6 no-shows, Gate #3 volume
  pool all read from this sheet.
- Implements the Smart Goal "Ensure the spreadsheet includes all key data
  points such as trip volume, no-show rates, and cost per hour".

### Sheet 4 — `Summary Preview` (visible)

Submission preview computed from the first two data sheets: Completed trips /
week, billable vs non-billable no-shows, estimated revenue, implied revenue
/ Kent-Leg, inferred volume class mix. Non-editable; formulas only.

**Maps to deliverables**
- Client-side "preview before submit" that matches the `IntakeSummaryPanel`
  component on the dashboard.
- Satisfies the Design-Doc requirement "flag missing or incomplete inputs
  before generating a decision".

### Sheet 5 — `Lists` (visible)

Validation vocabularies for drop-downs: Organization Type values (Hospital,
SNF, Health Plan, Broker, Community Organization, Behavioral Health, Other),
Volume Class (Quality / Filler / Broker / Other), Service Category, Trip
Mode, Higher-Acuity?, Rate Structure (Per Trip / Per Leg / Hourly /
Capitated / Other), Payer Type (Direct Facility / Health Plan / Broker /
Community Program / Other).

**Maps to deliverables**
- Same controlled vocabulary as
  [code/config/pjtl_kpis_and_formulas.json](../../config/pjtl_kpis_and_formulas.json).
  The web intake drop-downs and the backend schema are both generated from
  this list.
- Guarantees the intake matches the `Contract Volume` / `Revenue by Payer`
  sheets' taxonomy so the blending step is lossless.

---

## 3. `RideYourWay_Prospective_Market_Intake_Example.xlsx` — filled example

Same five sheets as the Template, populated for "Example Medical Center"
(submission ID `EX-CEO-001`, Hospital, Grand Rapids):

- `Start Here` — identical copy to template.
- `Organization Intake` — filled with example org + contact info.
- `Trip Demand Input` — 7 trip-pattern rows:
  1. ED / Inpatient Discharges — Ambulatory (18 completed / wk)
  2. ED / Inpatient Discharges — Wheelchair (14 completed / wk)
  3. Oncology & Specialist Recurring Appointments — Ambulatory (12 / wk)
  4. Dialysis Transportation Program — Wheelchair (24 / wk)
  5. Interfacility Transfers — Stretcher Alternative (5 / wk, **higher
     acuity**)
  6. Behavioral Health Secure Transport — SecureCare (4 / wk, **higher
     acuity**)
  7. Community Access Overflow — Ambulatory (8 / wk, filler)
- `Summary Preview` — 91 completed trips / week rollup.
- `Lists` — same vocabulary as template.

**Maps to deliverables**
- **Default demo payload** for the web app. The upload pipeline uses this
  file when the UI is exercised without a customer upload, guaranteeing the
  first-run dashboard has a realistic looking market.
- **Shape contract** consumed by
  [code/scripts/build_phase1_canonical_base.py](../../scripts/build_phase1_canonical_base.py).
  The offline pipeline asserts the customer's uploaded workbook has the same
  sheets, column headers, and drop-down vocabulary as this example.
- **Teaching aid** referenced in the 1/28 sync meeting: "Make excel
  spreadsheet for Detroit data gathering" was answered by shipping this
  concrete example so prospects understand the shape.

---

## 4. `PJTL Internal Meetings/Copy of RYW Gantt Chart W26.xlsx` — project tracker

**Not read by the app.** This is the student team's schedule.

### Sheet 1 — `Gantt Chart Template` (visible)

SMART-goals × subtasks × weekly progress grid (M/T/W/R/F columns per week).
Columns track SMART GOAL, SUBTASK TITLE, owner, "ON TIME?", then Week 1
through Week N grids starting 2026-01-12. Rows include Kick-Off (Initial
Meeting, Team In-Class Meetings, Data Team Meetings, Dashboard Team Meetings,
Metric Prioritization Discussion, Meetings with Tom/RYW), plus rocks for
Data Cleaning, Risk Matrix, Market Ready Dashboard, Projected Margin
Calculation.

**Maps to deliverables**
- Mirrors the EOS structure from `[RYW] Entrepreneur Operating System.docx`:
  each team member's Rocks → weekly milestones → IDS review.
- Crosses with the Smart Goals from the 1/19 meeting:
  1. **Market Readiness Dashboard** — Rock 3 in Emily's EOS doc (Weeks 6-10).
  2. **Market Viability Spreadsheet** — the intake template under
     [code/inputs/](../../inputs/).
  3. **Projected Margin Calculation** — the Weekly Margin logic wired into
     the readiness engine + the Margin Waterfall dashboard card.

### Sheet 2 — `Sheet2` (visible, empty)

Placeholder. Not used.

---

## Deliverable ↔ sheet matrix

The CEO's scope doc
(`Ride YourWay × PJTL Project Scope & Key Information.docx`) lists six
Student Deliverables. Here is the cross-reference.

| Deliverable | Primary sheets | Supporting sheets | Implemented in |
|---|---|---|---|
| Market Readiness Score / Dashboard | Q1 `Total Performance`, `Regional Performance`, `Weekly Margin`, `Mode Breakdown` | Q1 `Vehicle Breakdown`, `SecureCare Profit`, `Contract Volume`, `Revenue by Payer`, `OTP` | [code/frontend/pages/dashboard.vue](../../frontend/pages/dashboard.vue), [GateScorecard](../../frontend/components/GateScorecard.vue), [GateDetailPanel](../../frontend/components/GateDetailPanel.vue), [KpiSnapshotPanel](../../frontend/components/KpiSnapshotPanel.vue) |
| Prospective-market intake spreadsheet | Intake `Organization Intake`, `Trip Demand Input`, `Lists` | Intake `Start Here`, `Summary Preview` | [code/inputs/RideYourWay_Prospective_Market_Intake_Template.xlsx](../../inputs/RideYourWay_Prospective_Market_Intake_Template.xlsx) + the upload UI in [pages/market.vue](../../frontend/pages/market.vue) |
| Projected Margin Calculation | Q1 `Weekly Margin`, `SecureCare Profit` | Q1 `Vehicle Breakdown`, Intake `Trip Demand Input` | [MarginWaterfallPanel.vue](../../frontend/components/MarginWaterfallPanel.vue) + `engine/viability_service.py` |
| Identification of risk & constraint violations | Q1 `Total Performance`, `Regional Performance`, `Mode Breakdown`, `Contract Volume` | Q1 `Revenue by Payer`, `Weekly Margin` | [RiskMitigationPanel.vue](../../frontend/components/RiskMitigationPanel.vue), gate-evaluator logic |
| Recommended mitigation levers | All nine Q1 operational sheets | All Intake sheets | [SensitivityScenarioPanel.vue](../../frontend/components/SensitivityScenarioPanel.vue) + the XGBoost sliders |
| Scenario modeling (stretch) | Q1 `Contract Volume`, `Revenue by Payer`, `Weekly Margin` | All of the above | Inference sliders on [pages/index.vue](../../frontend/pages/index.vue) + `test_readiness_edge_cases.py` |

## Gate ↔ sheet matrix

The nine required conditions (scope doc §5), with the sheets that supply the
numerator and denominator for each.

| # | Gate (threshold) | Numerator sheet | Denominator / target sheet | Dashboard surface |
|---|---|---|---|---|
| 1 | Vehicle utilization ≥ 95 % | Q1 `Total Performance` (completed Kent-Legs) | Q1 `Total Performance` (Target Capacity) | Gate card #1 (RingStat) |
| 2 | Billed utilization ≥ 105 % | Q1 `Total Performance` / `Regional Performance` (billable-NS + completed) | Q1 `Total Performance` (Target Capacity) | Gate card #2 (RingStat) |
| 3 | Total volume pool ≥ 120 % | Q1 `Heat Map` (Ride Pool) | Q1 `Total Performance` (Target Capacity) × 1.3 Kent-Leg multiplier | Gate card #3 (BarStat) |
| 4 | Revenue / Kent-Leg ≥ $70 | Q1 `Revenue by Payer` (Order Price sum) | Q1 `Mode Breakdown` / `Contract Volume` (Kent-Leg sum) | Gate card #4 (BarStat + $ tile) |
| 5 | Higher-acuity mix ≥ 5 % | Q1 `Mode Breakdown` (Stretcher + SecureCare rows) | Q1 `Mode Breakdown` (total trips) | Gate card #5 (RingStat) |
| 6 | Non-billable no-shows ≤ 10 % | Q1 `Total Performance` (Non-Billable NS) | Q1 `Total Performance` (Total rides) | Gate card #6 (RingStat, inverse) |
| 7 | Road time ≥ 9 h / vehicle / day | Q1 `Vehicle Breakdown` (road time rows) | Q1 `Vehicle Breakdown` (vehicle count × 5 days) | Gate card #7 (BarStat) |
| 8 | No contract > 20 % volume or revenue | Q1 `Contract Volume` grouped by Payer ID, `Revenue by Payer` grouped by Payer ID | Q1 `Contract Volume` / `Revenue by Payer` (totals) | Gate card #8 (BarStat, concentration) |
| 9 | Cost / road hour ≤ $50 | Q1 `Weekly Margin` (Total Cost) + `SecureCare Profit` | Q1 `Vehicle Breakdown` (road hours) | Gate card #9 (BarStat + $ tile) |

## Module ↔ sheet matrix

The Design Doc (`PJTL Design /Detailed Map.docx`) decomposes the system into
seven modules. Here is the workbook evidence each module relies on.

| Module | Inputs from Q1 | Inputs from Intake | Notes |
|---|---|---|---|
| 1. Demand | `Contract Volume`, `Heat Map`, `Mode Breakdown` | `Trip Demand Input` | External market variables (population, facility density) are listed in the Design Doc as target (non-historical) inputs. |
| 2. Contract Business Model | `Contract Volume`, `Revenue by Payer`, `Total Performance`, `Regional Performance` | `Organization Intake` (payer type), `Trip Demand Input` (payer + billable-NS columns) | Billable-NS logic for SNF 100 % after-12h rule comes straight from the Internal Data Comments doc. |
| 3. Capacity & Scheduling | `Heat Map`, `Vehicle Breakdown`, `Total Performance`, `OTP` | `Trip Demand Input` | Overbooking cap (120–130 %) pulled from `Heat Map` Kent-Leg multiplier of 1.3. |
| 4. Cost | `Weekly Margin`, `SecureCare Profit`, `Vehicle Breakdown` | (none — internal cost model) | Driver-wage + gas coefficients (`0.9764…`, `0.1946…`) computed from historical cost ÷ total mileage. |
| 5. Revenue & Margin | `Revenue by Payer`, `Weekly Margin`, `SecureCare Profit` | `Trip Demand Input` | Expected revenue/Kent-Leg by mode + acuity lift from SecureCare sheet. |
| 6. Routing & Density (stretch) | `Heat Map`, `Contract Volume`, `Vehicle Breakdown` | (none) | Requires external data (weather, facility clustering) not present in any sheet. |
| 7. Risk / Sensitivity (stretch) | All of the above | All of the above | Implemented via the XGBoost sliders and the T1–T6 sensitivity harness — see [ml/sensitivity-harness.md](../ml/sensitivity-harness.md). |

## Meeting-decision ↔ sheet cross-reference

| Meeting / decision | Workbook evidence |
|---|---|
| 1/19 internal: binary Go / No-Go output | Gate totals from Q1 `Total Performance`, `Weekly Margin` → feed the readiness engine. |
| 1/19 internal: sheet-based intake for prospective sites | Created as `Intake_Template.xlsx` + `Intake_Example.xlsx`. |
| 1/21 RYW Sync #1: "Make excel spreadsheet for Detroit data gathering" | Same intake template — reusable per prospective market. |
| 1/21 RYW Sync #1: Wednesdays 10 AM / Fridays 2 PM cadence, Detroit next 6–8 months | Metadata only; no workbook change. |
| 1/28 RYW Sync #2: EOS rocks rollout | Tracked in the Gantt workbook, not a data input. |
| 2/2 Class Notes (Nancy Gay): "Use heat maps… red / yellow / green" | The RingStat microchart in `dashboard.vue` renders pass/provisional/fail with those tones; Q1 `Heat Map` sheet is the inspiration for the color-coded density panel. |
| Internal Data Comments — Kent-Leg formula `(miles − 8) / 23 + 1` | Implemented in the phase-1 build script; sourced from `Contract Volume` mileage and confirmed in `Mode Breakdown`. |
| Internal Data Comments — driver wage & cost source | `Weekly Margin` + `Vehicle Breakdown`. |
| Internal Data Comments — "we don't have weekly margin per site yet" | Explains why Gate #9 is currently computed at the fleet level, with per-region surfaced in v2. |
| RYW Questions Doc — 11 input categories (market, hospital/SNF, broker, community, operational, contract, revenue/cost, NS, higher-acuity, market-potential, tech-systems) | Categories 5–9 map to Q1 sheets; categories 1–4 and 10–11 are answered by the prospective-market Intake workbook. |

## Pipeline entry points

These are the exact commands and files that touch the workbooks. Keep them
in sync if you re-shape a sheet.

```bash
# 1. Extract Q1 + intake into canonical CSVs
python code/scripts/build_phase1_canonical_base.py
# outputs → code/intermediates/phase1/*.csv

# 2. Generate / rebuild the training rows used by XGBoost
python code/scripts/generate_readiness_training_rows.py
python code/scripts/build_readiness_training_base.py
# outputs → code/intermediates/training/readiness_training_rows.csv
#           code/intermediates/inference_inputs/readiness_training_base.csv

# 3. Upload-path live: POST /api/v1/jobs/upload with the customer's
#    RideYourWay_Prospective_Market_Intake_*.xlsx
#    (the backend runs build_phase1_canonical_base against the upload +
#    the bundled Q1 workbook inside the container's /workspace/code/).
```

| Sheet | Extracted to (under `code/intermediates/phase1/`) |
|---|---|
| `Total Performance` | `total_performance.csv`, folded into `minimum_viable_subset.csv` |
| `Regional Performance` | `regional_performance.csv` |
| `Mode Breakdown` | `mode_breakdown_base.csv`, `mode_summary_base.csv` |
| `OTP` | `otp_base.csv` |
| `Contract Volume` | `contract_volume_base.csv`, `quarantine_list.csv` (dirty rows) |
| `Heat Map` | `heat_map_base.csv` |
| `Revenue by Payer` | `payer_summary_base.csv` |
| `Weekly Margin` | `weekly_margin_base.csv` |
| `Vehicle Breakdown` | `driver_active_time_base.csv`, `vehicle_day_base.csv` |
| `SecureCare Profit` | `securecare_profit_base.csv` |
| `Corewell Metrics` (hidden) | — (intentionally skipped) |
| `Sheet2` (hidden) | — (intentionally skipped) |
| Intake `Organization Intake` | `prospective_intake_base.csv` (one-row summary) |
| Intake `Trip Demand Input` | `prospective_intake_base.csv` (trip-pattern rows) |
| Intake `Lists` | `field_dictionary.csv`, `unit_dictionary.csv` |
| Intake `Summary Preview`, `Start Here` | — (derived; not re-extracted) |

## What is *not* in these workbooks

To be explicit about gaps the meeting notes repeatedly flagged, documented so
nobody treats their absence as a bug:

- **Per-region weekly margin** — Q1 `Weekly Margin` is fleet-wide. Zach's
  comment: "Unfortunately, we don't currently have this data. We don't have
  the cost sector per region broken down yet but we could if that would be
  valuable." Gate #9 is therefore evaluated at fleet level.
- **External market variables** (population 65+, Medicaid %, facility
  density, competitor presence, road-network density, traffic-congestion
  index). These appear in the Design Doc's Module 1.1 / 1.2 / 1.3 but no
  sheet here ships them. They are marked as `target` inputs to be sourced
  from CMS, HIFLD, ACS, CDC PLACES when the system moves past the MVP.
- **SecureCare per-trip vehicle-level cost breakout**. The SecureCare Profit
  sheet rolls everything up; per-vehicle granularity will arrive with the
  Corewell pilot going live.
- **Weather / deadhead / dwell-time detail**. Design-doc Module 6 depends on
  it; Q1 only ships pickup time and mileage, so deadhead is currently
  inferred from the KL-per-road-hour ratio.

These gaps are the `targets` column in
[knowledge-base/assumption-register.md](../../../knowledge-base/assumption-register.md)
and the yellow / provisional badges on the corresponding gate cards.
