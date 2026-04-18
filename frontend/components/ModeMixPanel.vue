<script setup lang="ts">
/**
 * D3 — Mode profitability mix.
 *
 * Reads the Q1 base contract volume slice summarised in
 * ``mode_profitability.csv``: one row per order mode with trip counts, Kent-
 * Legs, revenue shares, average revenue/KL, miles, and no-show rates.
 *
 * Revenue-share bars and no-show-rate bars use the shared ``BarList`` style
 * tokens so it feels part of the rest of the dashboard. SecureCare is surfaced
 * inline via ``note`` because it lives on a separate sheet; the breakdown
 * mirrors what the narrative report cites.
 */
type Mode = {
  mode: string
  trip_count: number | null
  trip_share: number | null
  kent_legs: number | null
  kent_leg_share: number | null
  revenue: number | null
  revenue_share: number | null
  avg_revenue_per_trip: number | null
  avg_revenue_per_kentleg: number | null
  avg_miles: number | null
  nonbillable_ns_rate: number | null
  billable_ns_rate: number | null
  profit_margin: number | null
  total_cost: number | null
  note: string | null
}

const props = defineProps<{
  modes: Mode[]
  loading?: boolean
  error?: string | null
}>()

const baseModes = computed(() => props.modes.filter((m) => m.note === null || m.note === undefined || m.note === ""))
const annotatedModes = computed(() => props.modes.filter((m) => (m.note ?? "") !== ""))

const totalRevenue = computed(() =>
  baseModes.value.reduce((sum, m) => sum + (m.revenue ?? 0), 0)
)
const totalKentLegs = computed(() =>
  baseModes.value.reduce((sum, m) => sum + (m.kent_legs ?? 0), 0)
)

function pct(v: number | null): string {
  if (v === null || v === undefined) return "—"
  return `${(v * 100).toFixed(1)}%`
}
function currency(v: number | null): string {
  if (v === null || v === undefined) return "—"
  return `$${v.toLocaleString("en-US", { maximumFractionDigits: 0 })}`
}
function short(v: number | null): string {
  if (v === null || v === undefined) return "—"
  return v.toLocaleString("en-US", { maximumFractionDigits: 0 })
}

function revShareBar(mode: Mode): number {
  const share = mode.revenue_share ?? 0
  return Math.min(100, Math.max(0, share * 100))
}
function nsBar(mode: Mode): number {
  const share = mode.nonbillable_ns_rate ?? 0
  return Math.min(100, Math.max(0, share * 100))
}
function nsTone(mode: Mode): string {
  if (mode.nonbillable_ns_rate === null || mode.nonbillable_ns_rate === undefined) return "neutral"
  return mode.nonbillable_ns_rate <= 0.1 ? "pass" : "fail"
}
</script>

<template>
  <section class="panel ops-panel">
    <header class="ops-panel__head">
      <div class="panel-eyebrow">
        D3: Mode profitability
        <InfoTip
          label="Mode profitability"
          content="Trip-level aggregates from contract_volume_base.csv grouped by order_mode. Kent-Leg share is trips × mileage-derived legs; revenue per KL compares each mode to the $70 gate-4 target. SecureCare rows come from the SecureCare sheet (weeks 1-5 margin + no-show summary) and appear alongside the base fleet modes for a full fleet mix."
        />
      </div>
      <h2>Mode mix &amp; profitability</h2>
      <p class="ops-panel__caption">
        Fleet Q1 aggregate: {{ short(totalKentLegs) }} Kent-Legs · {{ currency(totalRevenue) }} revenue across {{ baseModes.length }} modes.
      </p>
    </header>

    <div v-if="loading" class="ops-panel__status">Loading mode mix…</div>
    <div v-else-if="error" class="ops-panel__status ops-panel__status--error">{{ error }}</div>
    <div v-else-if="!modes.length" class="ops-panel__status">No mode data. Run the operational EDA notebook.</div>

    <ul v-else class="mode-list">
      <li v-for="m in baseModes" :key="m.mode" class="mode-card">
        <div class="mode-card__head">
          <div class="mode-card__name">{{ m.mode }}</div>
          <div class="mode-card__stats">
            <span>{{ short(m.trip_count) }} trips</span>
            <span>{{ short(m.kent_legs) }} KL</span>
            <span>{{ currency(m.revenue) }} rev</span>
          </div>
        </div>

        <div class="mode-row">
          <span class="mode-row__label">Revenue share</span>
          <div class="mode-bar">
            <div class="mode-bar__fill mode-bar__fill--rev" :style="{ width: `${revShareBar(m)}%` }" />
          </div>
          <strong class="mode-row__value">{{ pct(m.revenue_share) }}</strong>
        </div>

        <div class="mode-row">
          <span class="mode-row__label">Non-billable no-shows</span>
          <div class="mode-bar">
            <div
              class="mode-bar__fill"
              :class="`mode-bar__fill--${nsTone(m)}`"
              :style="{ width: `${nsBar(m)}%` }"
            />
          </div>
          <strong class="mode-row__value" :class="`mode-row__value--${nsTone(m)}`">{{ pct(m.nonbillable_ns_rate) }}</strong>
        </div>

        <dl class="mode-meta">
          <div>
            <dt>Rev / KL</dt>
            <dd>{{ currency(m.avg_revenue_per_kentleg) }}</dd>
          </div>
          <div>
            <dt>Rev / trip</dt>
            <dd>{{ currency(m.avg_revenue_per_trip) }}</dd>
          </div>
          <div>
            <dt>Avg miles</dt>
            <dd>{{ m.avg_miles === null ? "—" : m.avg_miles.toFixed(1) }}</dd>
          </div>
        </dl>
      </li>
    </ul>

    <div v-if="annotatedModes.length" class="securecare-block">
      <div class="panel-eyebrow">SecureCare stream</div>
      <ul class="mode-list mode-list--compact">
        <li v-for="m in annotatedModes" :key="m.mode" class="mode-card mode-card--securecare">
          <div class="mode-card__head">
            <div class="mode-card__name">{{ m.mode }}</div>
            <div class="mode-card__stats">
              <span v-if="m.trip_count !== null">{{ short(m.trip_count) }} trips</span>
              <span v-if="m.revenue !== null">{{ currency(m.revenue) }} rev</span>
              <span v-if="m.total_cost !== null">{{ currency(m.total_cost) }} cost</span>
            </div>
          </div>
          <dl class="mode-meta mode-meta--wide">
            <div v-if="m.profit_margin !== null">
              <dt>Profit margin</dt>
              <dd>{{ pct(m.profit_margin) }}</dd>
            </div>
            <div v-if="m.nonbillable_ns_rate !== null">
              <dt>No-show rate</dt>
              <dd>{{ pct(m.nonbillable_ns_rate) }}</dd>
            </div>
          </dl>
          <p v-if="m.note" class="mode-note">{{ m.note }}</p>
        </li>
      </ul>
    </div>
  </section>
</template>

<style scoped>
.ops-panel { padding: 20px 22px; }
.ops-panel__head { margin-bottom: 10px; }
.ops-panel h2 {
  margin: 4px 0 2px;
  font-size: clamp(1.1rem, 1.6vw, 1.35rem);
  letter-spacing: -0.02em;
}
.ops-panel__caption {
  margin: 2px 0 10px;
  color: var(--muted);
  font-size: 0.85rem;
}
.ops-panel__status {
  padding: 10px 12px;
  color: var(--muted);
  font-size: 0.9rem;
}
.ops-panel__status--error { color: var(--red); }

.mode-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 10px;
}
.mode-list--compact { margin-top: 8px; }

.mode-card {
  padding: 12px 14px;
  border: 1px solid var(--line);
  border-radius: 14px;
  background: var(--surface-2);
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.mode-card--securecare {
  border-color: color-mix(in srgb, var(--teal) 40%, var(--line));
  background: color-mix(in srgb, var(--teal-soft) 55%, var(--surface-2));
}

.mode-card__head {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  align-items: baseline;
  flex-wrap: wrap;
}
.mode-card__name {
  font-weight: 700;
  font-size: 0.98rem;
}
.mode-card__stats {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  font-size: 0.78rem;
  color: var(--muted);
  font-variant-numeric: tabular-nums;
}

.mode-row {
  display: grid;
  grid-template-columns: 1fr 2.1fr auto;
  gap: 8px;
  align-items: center;
  font-size: 0.82rem;
}
.mode-row__label {
  color: var(--muted);
}
.mode-row__value {
  font-variant-numeric: tabular-nums;
  font-weight: 700;
}
.mode-row__value--fail { color: var(--red); }
.mode-row__value--pass { color: var(--teal); }

.mode-bar {
  height: 7px;
  border-radius: 999px;
  background: var(--surface);
  border: 1px solid var(--line);
  overflow: hidden;
  position: relative;
}
.mode-bar__fill {
  height: 100%;
  transition: width 240ms ease;
  border-radius: 999px;
}
.mode-bar__fill--rev {
  background: linear-gradient(90deg, var(--blue), var(--maize));
}
.mode-bar__fill--pass { background: var(--teal); }
.mode-bar__fill--fail { background: var(--red); }
.mode-bar__fill--neutral { background: var(--line-strong); }

.mode-meta {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
  margin: 0;
  padding-top: 4px;
  border-top: 1px dashed var(--line);
}
.mode-meta--wide {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}
.mode-meta dt {
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--muted);
  font-weight: 700;
}
.mode-meta dd {
  margin: 2px 0 0;
  font-size: 0.92rem;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.securecare-block {
  margin-top: 14px;
}
.mode-note {
  margin: 4px 0 0;
  font-size: 0.8rem;
  color: var(--muted);
  line-height: 1.45;
}
</style>
