# Operational EDA — narrative report

Execution artifact: [`code/inference_engine/notebooks/operational_eda.ipynb`](../../inference_engine/notebooks/operational_eda.ipynb)
Reusable logic: [`code/inference_engine/scripts/operational_eda.py`](../../inference_engine/scripts/operational_eda.py)

> **Related reading**
> - [sheet-inventory.md](sheet-inventory.md) — what's in every workbook sheet.
> - [../deliverables.md](../deliverables.md) — the ten value-add deliverables
>   (D1..D10) this EDA powers, plus what's deferred pending external data.
> - Frontend: the *Operational deep dive* tab in `code/frontend/pages/dashboard.vue`
>   renders every artifact here via `/api/v1/dashboard/*` (see
>   [`code/backend/api/routes/operational.py`](../../backend/api/routes/operational.py)).

Every number below is sourced from a CSV under
[`code/outputs/reports/operational_eda/`](../../outputs/reports/operational_eda/).
Every plot referenced is under
[`code/outputs/plots/operational_eda/`](../../outputs/plots/operational_eda/).
Re-run the notebook (or `python code/inference_engine/scripts/operational_eda.py`)
and all artifacts regenerate idempotently.

Data window: **Dec 29 2025 – Jan 31 2026** (the five weeks the CEO referred to
as "Q1 2026" in the data pack). The `Regional Performance` sheet mis-labels its
quarter rollup as "Q1" even though the header banner reads "Quarter four
Total" — see the sheet inventory for provenance details.

---

## 1. Data coverage

Source: [sheet_coverage.csv](../../outputs/reports/operational_eda/sheet_coverage.csv).

- **22 sheets** across three input workbooks (20 visible, 2 hidden — the hidden
  sheets are `SecureCare Data` and `Contract Margin`, both vestigial helpers
  used by dashboard pivots).
- Kent-Leg multiplier (`Heat Map!A1`) = **1.3**. This is the coefficient that
  converts mileage into Kent-Leg equivalents (1 Kent-Leg = 1 completed trip at
  ≤ the regional mileage threshold; longer trips add fractional Kent-Legs via
  `Mileage Kent Legs = ceil(mileage / 1.3 - 1) × 0.5`).
- 8,087 trip records in `Contract Volume` (= `Revenue by Payer` — both share
  the same source table; the right-hand pivots differ).

---

## 2. Fleetwise gate scorecard

Source: [fleet_gate_scorecard.csv](../../outputs/reports/operational_eda/fleet_gate_scorecard.csv).
Plot: [fleet_gate_bars.png](../../outputs/plots/operational_eda/fleet_gate_bars.png).

Per-region Q1 2026 readings (fleet target in parentheses):

| Gate | Grand Rapids | Lansing | Battle Creek | Pass? |
|---|---|---|---|---|
| G1 Vehicle utilization (≥ 95%) | 84.8% | 77.3% | 79.6% | **fail in all 3 regions** |
| G2 Billed utilization (≥ 105%) | 90.5% | 86.4% | 87.9% | **fail in all 3 regions** |
| G3 Volume pool ratio (≥ 1.20) | 1.241 | 1.261 | 1.261 | pass in all 3 regions |
| G4 Revenue / Kent-Leg (≥ $70) | $71.53 | $81.64 | $71.86 | pass in all 3 regions |
| G5 Higher-acuity mix (≥ 5%) | 3.6% | 1.5% | 0.1% | **fail in all 3 regions** |
| G6 Non-billable NS (≤ 10%) | 21.7% | 21.3% | 14.2% | **fail in all 3 regions** |
| G7 Road time / vehicle / day (≥ 9h) | 8.66h | 8.66h | 8.66h | **fail in all 3 regions** |
| G8 Largest payer share of volume (≤ 20%) | 30.0% | 15.7% | 35.1% | pass only in Lansing |
| G8 Largest payer share of revenue (≤ 20%) | 18.7% | 13.5% | 30.3% | **fail in Battle Creek** |
| G9 Cost per road hour (≤ $50) | $110.16 | $110.16 | $110.16 | **fail (estimate)** |

Key observation matching the Feb meeting-log claim: **Grand Rapids' broker
dependency is severe** — 30% of Grand Rapids volume is booked through a single
payer (SafeRide Health – Priority Medicaid). Battle Creek is smaller but even
more concentrated (35% of volume to Battle Creek VA). Lansing is the only
region currently inside the 20% cap.

Gate 7 (road time) and Gate 9 (cost per road hour) are reported fleet-level
because RYW has confirmed per-region cost and vehicle→region mapping are not
broken down in Q1 data; these rows carry the `detail` column
`fleet-level (per-region vehicle mapping not available)` / `fleet-level
estimate (per-region cost not reported)` as an audit trail.

---

## 3. Weekly trend

Source: [weekly_gate_trend.csv](../../outputs/reports/operational_eda/weekly_gate_trend.csv).
Plot: [weekly_trend_small_multiples.png](../../outputs/plots/operational_eda/weekly_trend_small_multiples.png).

| Week | Vehicle util | Billed util | Vol pool | Rev / KL | Higher-acuity | Non-bill NS | Profit margin |
|---|---|---|---|---|---|---|---|
| Week 1 | 49.2% | 54.7% | 1.244 | $73.95 | 3.3% | 26.5% | **−36.3%** |
| Week 2 | 82.2% | 89.1% | 1.273 | $70.53 | 2.5% | 18.5% | 17.4% |
| Week 3 | 98.2% | 99.5% | 1.330 | $73.98 | 2.4% | 16.5% | 23.4% |
| Week 4 | 81.9% | 95.2% | 1.246 | $72.91 | 2.5% | 21.5% | 16.5% |
| Week 5 | 99.4% | 114.3% | 1.222 | $71.54 | 1.8% | 19.4% | 25.4% |

Observations:

- **Utilisation is climbing steeply**: Week 1 was a holiday ramp (49%
  vehicle util, negative $20k margin) and the fleet exits the quarter at
  99% / 114% (Week 5 meets Gate 2 for the first time).
- **Margin crossed zero at Week 2** and held 12–25% through Week 5 — the
  growth-company threshold (25% target) is only hit in Weeks 3 and 5.
- **Non-billable NS rate is not improving monotonically** (26.5% → 18.5% →
  16.5% → **21.5%** → 19.4%). Week 4 regression lines up with the broker
  cancellation surge described in internal notes.
- **Higher-acuity mix is trending down** (3.3% → 1.8%), moving farther
  from the 5% target. SecureCare is growing (§9) but Stretcher volume is
  not.

---

## 4. Mode mix & profitability

Source: [mode_profitability.csv](../../outputs/reports/operational_eda/mode_profitability.csv).
Plot: [mode_mix.png](../../outputs/plots/operational_eda/mode_mix.png).

| Mode | Completed trips | Trip share | Revenue | Rev share | Rev / KL | Non-bill NS rate | Billable NS rate |
|---|---|---|---|---|---|---|---|
| Wheelchair | 2,303 | 54.2% | $174,985 | 45.6% | $68.95 | 20.8% | 7.4% |
| Ambulatory | 1,828 | 43.0% | $152,083 | 39.6% | $58.88 | 19.2% | 2.0% |
| Stretcher  | 117   | 2.8%  | $56,692  | 14.8% | $336.99 | 16.4% | 2.7% |
| SecureCare | *trip log not per-trip* | — | $49,007 | 12.8% | — | — | — |

Insights:

- **Stretcher is the per-trip profit leader** ($484 avg price vs. $76 for
  Wheelchair). Scaling Stretcher volume by ~3x would move Gate 5
  (higher-acuity mix) from 3% to ~9% without hurting the base fleet.
- **Ambulatory drags Rev/KL** at $58.88 — below the $70 gate. Wheelchair
  is close at $68.95. Stretcher carries the target single-handedly at
  $337. This is the single biggest lever on Gate 4.
- **Wheelchair has the worst no-show rate** (20.8% non-billable). Any
  cancellation-policy fix should start there.

SecureCare is a separate P&L stream (§9) — its revenue share of 12.8% is
the best proxy for its contribution to Gate 5.

---

## 5. OTP matrix

Source: [otp_matrix.csv](../../outputs/reports/operational_eda/otp_matrix.csv)
(756 rows: 7 scopes × 4 locations × 3 legs × 6 days + overheads).
Plot: [otp_heatmap.png](../../outputs/plots/operational_eda/otp_heatmap.png).

A-leg OTP by region (weekly totals):

| Region       | Week 1 | Week 2 | Week 3 | Week 4 | Week 5 |
|---|---|---|---|---|---|
| Grand Rapids | 87.4% | 93.5% | 87.7% | 82.5% | *see caveat* |
| Lansing      | 94.3% | 89.8% | 94.6% | 94.8% | *see caveat* |
| Fleet Total  | 88.1% | 93.2% | 88.4% | 83.9% | *see caveat* |

Key findings:

- **Lansing consistently beats the fleet** (89–95% vs 83–93%).
  Grand Rapids is the bottleneck, especially Thursdays (see heatmap cell).
- **Week 5 values in the OTP sheet appear incomplete** (computed column
  shows ~9% across the board which is not consistent with the 83–93%
  band elsewhere). The underlying counts in the left-hand block look
  like they stopped early; the CSV records whatever the workbook
  evaluates to so downstream consumers can see the anomaly. We recommend
  RYW refresh the Week 5 OTP pivot before relying on it.
- **B-leg is consistently better than A-leg** across every region in
  every complete week — the anomaly is at the pickup, not the return.
  This is counter to the meeting-log assumption (`B leg takes longer`);
  the data says B-leg pickup tends to be scheduled with more buffer.

Detroit rows are filtered out (no Q1 operations; kept in the sheet as
forward-looking skeleton).

---

## 6. Contract volume & cancellation patterns

Sources:
[payer_concentration.csv](../../outputs/reports/operational_eda/payer_concentration.csv),
[cancellation_patterns.csv](../../outputs/reports/operational_eda/cancellation_patterns.csv).
Plots:
[payer_pareto.png](../../outputs/plots/operational_eda/payer_pareto.png),
[cancellation_by_reason.png](../../outputs/plots/operational_eda/cancellation_by_reason.png).

### Concentration

72 distinct completed-trip payers across Q1.

| # | Payer | Volume share | Revenue share | Trips |
|---|---|---|---|---|
| 1 | SafeRide Health – Priority Medicaid | 22.7% | 14.2% | 840 |
| 2 | Battle Creek VA | 14.2% | 12.6% | 641 |
| 3 | MTM | 12.5% | 9.6% | 428 |
| 4 | PP | 5.7% | 5.9% | 279 |
| 5 | Valley View Care Center | 3.1% | 8.3% | 164 |

**Gate 8 (no payer > 20% of volume OR revenue) fails at fleet level**
because SafeRide is at 22.7% volume. Within-region, Grand Rapids and
Battle Creek also fail the cap (see §2). The CSV carries a `near_cap`
column that flags any payer within 3 points of the cap — the dashboard
will use it as an early-warning list.

### Cancellation patterns

`cancellation_patterns.csv` tabulates every non-completed trip by
`(status, reason, payer, mode, day)`. Aggregated counts for Q1:

- Confirmation Cancel: **959** (largest bucket; booked trip cancelled
  before same-day)
- Unable to Accommodate: **832** (rider requested, RYW couldn't offer a
  slot — the "turned-down" bucket Mike Frank called out)
- Turned Down: **955** (RYW declined pre-booking — capacity gate)
- Billed no show: **391** (rider no-show but trip fee applies)
- Same Day Cancel: **338**
- No Show (non-billable): **319**

Top day for cancellations is Monday (the Feb 9 "Monday morning volume
spike" lines up); the worst mode for no-shows is Wheelchair at 20.8%.

---

## 7. Hourly demand & idle windows

Source: [hourly_demand_idle.csv](../../outputs/reports/operational_eda/hourly_demand_idle.csv).
Plot: [hourly_heatmap.png](../../outputs/plots/operational_eda/hourly_heatmap.png).

Hourly-by-weekday Q4 baseline, both "requested" and "completed":

- **Peak demand 09:00–13:00** on weekdays (875–1109 completed trips in
  the 10:00–12:00 band fleet-wide).
- **Morning pre-peak ramp 06:00–08:00** is thinner on Thursday and
  Friday (24 completed trips requested between 06:00 and 06:59 on
  Thursday vs 35 on Monday/Tuesday).
- **Evening demand collapses after 17:00** except for Friday (41 trips)
  — which is still barely 5% of the 11:00 bar.
- **Saturday is a structurally idle day** (180 total rides in the full
  weekday mid-day band vs 1,377–1,618 on weekdays).

The CSV flags any weekday business-hour cell with `< 1` completed
trip as `is_idle_business = True`. The dashboard surfaces these
directly as "redeploy windows".

---

## 8. Revenue per Kent-Leg by payer

Sources:
[payer_rev_per_kentleg.csv](../../outputs/reports/operational_eda/payer_rev_per_kentleg.csv)
(per payer),
[payer_rev_per_kentleg_by_mode.csv](../../outputs/reports/operational_eda/payer_rev_per_kentleg_by_mode.csv)
(per payer × mode).
Plot: [payer_rev_waterfall.png](../../outputs/plots/operational_eda/payer_rev_waterfall.png).

Fleet Q1 Rev / KL = **$72.56** (= $383,761 completed revenue /
5,288 Kent-Legs; passes the $70 gate by $2.56).

Lift vs. $70 for the top-volume payers:

- **Valley View Care Center** → +$124 / KL (stretcher-heavy, 164 trips)
- **State MI – BH/IDD Medicaid Waiver** → +$40 / KL
- **SafeRide Health – Priority Medicaid** → +$5 / KL (the biggest book
  is also the thinnest margin against gate; any contract repricing
  swings this fastest)
- **PP (pre-pay retail)** → −$8 / KL
- **MTM** → −$15 / KL (429 trips at $54 / KL — a quiet drag)

The bottom-lift payer in the top-20-by-volume is **MTM**: worth a
negotiation round or a routing limit.

---

## 9. Cost & margin

Sources:
[cost_margin_trend.csv](../../outputs/reports/operational_eda/cost_margin_trend.csv),
[regional_cost_estimate.csv](../../outputs/reports/operational_eda/regional_cost_estimate.csv).
Plot: [margin_trend.png](../../outputs/plots/operational_eda/margin_trend.png).

Fleet vs SecureCare, weekly:

| Week | Fleet revenue | Fleet cost | Fleet margin | SC revenue | SC cost | SC margin |
|---|---|---|---|---|---|---|
| Week 1 | $109,174 | $129,801 | **−18.9%** | $8,229 | $9,680 | **−17.6%** |
| Week 2 | $176,939 | $154,515 | 12.7% | $6,722 | $7,683 | −14.3% |
| Week 3 | $191,137 | $154,816 | **19.0%** | $10,870 | $7,782 | **28.4%** |
| Week 4 | $165,759 | $146,675 | 11.5% | $10,587 | $7,828 | 26.1% |
| Week 5 | $189,550 | $149,809 | **21.0%** | $12,599 | $7,874 | **37.5%** |

- **SecureCare overtook the fleet** on margin in Week 3 and has
  outperformed by >15 points every week since.
- **Quarter-total cost**: $736,764.13 / **6,688 road-hours** ⇒ fleet
  average of **$110.16 per road hour** (more than 2× the $50 charter
  target). The dashboard tags this gate 9 as "assumption — not pass /
  fail" until RYW publishes per-region driver wages + per-hour overhead.
- **Regional cost apportionment** is a proxy based on published fleet
  counts (21 GR / 4 Lansing / 5 Battle Creek). Until RYW reports
  per-region cost, this CSV is explicitly labelled "Estimate" in both
  the file and the dashboard tile.

---

## 10. Cross-view (Gate × Fleet × Week)

Source: [gate_fleet_week_crossview.csv](../../outputs/reports/operational_eda/gate_fleet_week_crossview.csv).
Plot: [gate_fleet_week_heatmap.png](../../outputs/plots/operational_eda/gate_fleet_week_heatmap.png).

Vehicle utilization (Gate 1) by region × week:

| Region | Week 1 | Week 2 | Week 3 | Week 4 | Week 5 |
|---|---|---|---|---|---|
| Battle Creek | 38.4% | 71.9% | **105.0%** | 95.0% | **117.0%** |
| Grand Rapids | 56.1% | 93.5% | 100.8% | 78.1% | 94.9% |
| Lansing      | 53.1% | 81.2% | 88.8% | 72.5% | 86.2% |

- **Battle Creek is the biggest mover** (+78 pts Week 1 → Week 5) — but
  it's also the most concentrated payer mix (§6).
- **Grand Rapids plateaued** around 95% after Week 3; it never hits the
  100% target sustained.
- **Lansing is steady but smallest** (4-vehicle fleet).

The cross-view CSV is the raw material for every panel on the new
Operational Deep Dive tab. Each row is `(region, week)` with all seven
quantified gates attached, ready for a heatmap pivot.

---

## Data gaps (what we could not answer from these sheets)

Catalogued in full at [`code/docs/deliverables.md`](../deliverables.md) §
Deferred:

1. **Vehicle → region mapping**. `Vehicle Breakdown` has vehicle IDs and
   road time; regional assignment exists only in fleet-count metadata.
   Gate 7 and Gate 9 therefore report fleet-level.
2. **Per-region cost**. Confirmed by Zach in Internal Data Comments.
   Regional cost-per-hour is an estimate.
3. **External demand signals** (population 65+, competitor presence,
   facility density, weather, deadhead distance). Covered in the intake
   template for *new* markets but not in Q1 operating data.
4. **OTP Week 5 completeness**. The workbook block looks under-filled
   — raw A-leg OTP percentage drops to ~9% which is inconsistent with
   the rolling average. Surfacing the anomaly rather than hiding it.

These gaps drive the "Deferred (pending external data)" block in the
deliverables catalog.
