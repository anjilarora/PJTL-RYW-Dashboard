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
const chartEl = ref<HTMLElement | null>(null)
let hcLib: any = null
let hcChart: any = null

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

async function ensureHighcharts() {
  if (!import.meta.client) return
  if (!hcLib) hcLib = (await import("highcharts")).default
}

function renderChart() {
  if (!import.meta.client || !hcLib || !chartEl.value) return
  if (!baseModes.value.length) return
  const categories = baseModes.value.map((m) => m.mode)
  const revShare = baseModes.value.map((m) => (m.revenue_share == null ? null : Number((m.revenue_share * 100).toFixed(2))))
  const noShow = baseModes.value.map((m) => (m.nonbillable_ns_rate == null ? null : Number((m.nonbillable_ns_rate * 100).toFixed(2))))
  const revPerKl = baseModes.value.map((m) => (m.avg_revenue_per_kentleg == null ? null : Number(m.avg_revenue_per_kentleg.toFixed(2))))
  if (hcChart) hcChart.destroy()
  hcChart = hcLib.chart(chartEl.value, {
    chart: {
      type: "column",
      backgroundColor: "transparent",
      spacingTop: 12,
      spacingRight: 12,
      spacingLeft: 8,
      spacingBottom: 8,
      animation: { duration: 260 }
    },
    title: { text: undefined },
    credits: { enabled: false },
    xAxis: {
      categories,
      lineColor: "rgba(152,164,183,0.25)",
      tickColor: "rgba(152,164,183,0.25)",
      labels: { style: { color: "#98a4b7", fontSize: "11px" } }
    },
    yAxis: [{
      title: { text: "Share / No-show (%)", style: { color: "#98a4b7" } },
      labels: { style: { color: "#98a4b7", fontSize: "11px" } },
      gridLineColor: "rgba(152,164,183,0.16)",
      max: 100
    }, {
      title: { text: "Rev / KL ($)", style: { color: "#98a4b7" } },
      labels: { style: { color: "#98a4b7", fontSize: "11px" } },
      opposite: true,
      gridLineWidth: 0,
      plotLines: [{
        value: 70,
        color: "rgba(255,203,5,0.9)",
        width: 1.2,
        dashStyle: "Dash",
        label: {
          text: "Target $70",
          align: "right",
          style: { color: "#ffc873", fontWeight: "700", fontSize: "10px" }
        }
      }]
    }],
    tooltip: {
      shared: true,
      borderColor: "rgba(152,164,183,0.28)",
      backgroundColor: "rgba(15,20,28,0.95)",
      style: { color: "#f4f7fb" },
      formatter: function (this: any) {
        const idx = this.points?.[0]?.point?.index ?? 0
        const mode = categories[idx] ?? ""
        const trips = short(baseModes.value[idx]?.trip_count ?? null)
        const rev = currency(baseModes.value[idx]?.revenue ?? null)
        const revKl = currency(baseModes.value[idx]?.avg_revenue_per_kentleg ?? null)
        const share = pct(baseModes.value[idx]?.revenue_share ?? null)
        const ns = pct(baseModes.value[idx]?.nonbillable_ns_rate ?? null)
        return `<b>${mode}</b><br/>Trips: <b>${trips}</b><br/>Revenue: <b>${rev}</b><br/>Revenue share: <b>${share}</b><br/>Non-billable NS: <b>${ns}</b><br/>Rev/KL: <b>${revKl}</b>`
      }
    },
    legend: {
      itemStyle: { color: "#98a4b7", fontSize: "11px" }
    },
    plotOptions: {
      column: {
        borderRadius: 6,
        borderWidth: 0,
        pointPadding: 0.08,
        groupPadding: 0.16
      },
      spline: {
        lineWidth: 2.2,
        marker: { enabled: true, radius: 4 }
      }
    },
    series: [
      { type: "column", name: "Revenue share (%)", data: revShare, color: "#5b9bff" },
      { type: "column", name: "Non-billable no-show (%)", data: noShow, color: "#ff6f78" },
      { type: "spline", name: "Revenue / KL ($)", yAxis: 1, data: revPerKl, color: "#35d39c" }
    ]
  })
}

onMounted(async () => {
  await ensureHighcharts()
  renderChart()
})

watch(
  [() => props.modes],
  () => {
    renderChart()
  },
  { deep: true }
)

onBeforeUnmount(() => {
  if (hcChart) hcChart.destroy()
})
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

    <div v-if="loading" class="ops-panel__status ops-panel__status--skeleton" aria-live="polite">
      <div class="skeleton skeleton-line" />
      <div class="skeleton skeleton-block" />
    </div>
    <div v-else-if="error" class="ops-panel__status ops-panel__status--error">{{ error }}</div>
    <div v-else-if="!modes.length" class="ops-panel__status">No mode data. Run the operational EDA notebook.</div>

    <template v-else>
      <div class="chart-wrap">
        <div ref="chartEl" class="mode-chart" />
      </div>
      <ul class="mode-list">
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
    </template>
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
.ops-panel__status--skeleton {
  display: grid;
  gap: 8px;
}
.chart-wrap {
  background: var(--surface-2);
  border: 1px solid var(--line);
  border-radius: 14px;
  padding: 10px;
  margin-bottom: 10px;
}
.mode-chart {
  width: 100%;
  min-height: 290px;
}
.skeleton-line {
  height: 12px;
  width: 60%;
}
.skeleton-block {
  height: 170px;
}

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
  transition: border-color 160ms ease, transform 160ms ease;
}
.mode-card:hover {
  border-color: color-mix(in srgb, var(--blue) 28%, var(--line));
  transform: translateY(-1px);
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
