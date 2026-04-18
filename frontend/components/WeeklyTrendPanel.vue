<script setup lang="ts">
/**
 * D2 — Weekly trend.
 *
 * Five-week metric history rendered as a metric picker plus compact SVG
 * sparkline. WoW arrows come directly from ``weekly_gate_trend.csv``.
 */
type Week = {
  week: string
  vehicle_usage: number | null
  billed_usage: number | null
  volume_pool_ratio: number | null
  otp: number | null
  revenue_per_kentleg: number | null
  higher_acuity_mix: number | null
  nonbillable_ns_rate: number | null
  largest_payer_vol: number | null
  largest_payer_rev: number | null
  total_revenue: number | null
  total_cost: number | null
  profit_margin: number | null
  vehicle_usage_wow: number | null
  billed_usage_wow: number | null
  volume_pool_ratio_wow: number | null
  otp_wow: number | null
  revenue_per_kentleg_wow: number | null
  higher_acuity_mix_wow: number | null
  nonbillable_ns_rate_wow: number | null
  largest_payer_vol_wow: number | null
  largest_payer_rev_wow: number | null
  profit_margin_wow: number | null
  largest_payer_vol_name: string | null
  largest_payer_rev_name: string | null
}

const props = defineProps<{
  weeks: Week[]
  loading?: boolean
  error?: string | null
}>()

type MetricKey =
  | "vehicle_usage"
  | "billed_usage"
  | "volume_pool_ratio"
  | "otp"
  | "revenue_per_kentleg"
  | "nonbillable_ns_rate"
  | "profit_margin"

type MetricSpec = {
  key: MetricKey
  label: string
  target: number
  comparator: "ge" | "le"
  format: "pct" | "ratio" | "currency"
  description: string
}

const metrics: MetricSpec[] = [
  {
    key: "vehicle_usage",
    label: "Vehicle utilization",
    target: 0.95,
    comparator: "ge",
    format: "pct",
    description: "Share of active vehicles on the road. Gate 1 target: ≥ 95%."
  },
  {
    key: "billed_usage",
    label: "Billed utilization",
    target: 1.05,
    comparator: "ge",
    format: "pct",
    description: "Billed Kent-Legs vs. available capacity. Gate 2 target: ≥ 105%."
  },
  {
    key: "volume_pool_ratio",
    label: "Volume pool ratio",
    target: 1.2,
    comparator: "ge",
    format: "ratio",
    description: "SKL divided by weekly target. Gate 3 target: ≥ 1.20."
  },
  {
    key: "otp",
    label: "On-time performance",
    target: 0.9,
    comparator: "ge",
    format: "pct",
    description: "Percentage of legs delivered on time across all regions and days."
  },
  {
    key: "revenue_per_kentleg",
    label: "Revenue / Kent-Leg",
    target: 70,
    comparator: "ge",
    format: "currency",
    description: "Fleet-wide blended revenue per Kent-Leg. Gate 4 target: ≥ $70."
  },
  {
    key: "nonbillable_ns_rate",
    label: "Non-billable no-shows",
    target: 0.1,
    comparator: "le",
    format: "pct",
    description: "Share of scheduled legs that became unpaid no-shows. Gate 6 target: ≤ 10%."
  },
  {
    key: "profit_margin",
    label: "Profit margin",
    target: 0.1,
    comparator: "ge",
    format: "pct",
    description: "Weekly (revenue - cost) / revenue from the fleet margin extract. Stretch target: ≥ 10%."
  }
]

const activeKey = ref<MetricKey>("vehicle_usage")
const activeSpec = computed<MetricSpec>(() => metrics.find((m) => m.key === activeKey.value) ?? metrics[0])

function fmtValue(spec: MetricSpec, v: number | null): string {
  if (v === null || v === undefined) return "—"
  if (spec.format === "pct") return `${(v * 100).toFixed(1)}%`
  if (spec.format === "currency") return `$${v.toFixed(1)}`
  return v.toFixed(2)
}

function fmtDelta(spec: MetricSpec, delta: number | null): string {
  if (delta === null || delta === undefined) return ""
  const sign = delta > 0 ? "+" : ""
  if (spec.format === "pct") return `${sign}${(delta * 100).toFixed(1)} pp`
  if (spec.format === "currency") return `${sign}$${delta.toFixed(1)}`
  return `${sign}${delta.toFixed(3)}`
}

function deltaTone(spec: MetricSpec, delta: number | null): string {
  if (delta === null || delta === undefined) return "neutral"
  if (delta === 0) return "neutral"
  const improving = spec.comparator === "ge" ? delta > 0 : delta < 0
  return improving ? "pass" : "fail"
}

const activeSeries = computed(() => props.weeks.map((w) => ({ week: w.week, value: w[activeSpec.value.key] as number | null })))
const wowSeries = computed(() =>
  props.weeks.map((w) => ({ week: w.week, value: w[`${activeSpec.value.key}_wow` as keyof Week] as number | null }))
)

// Chart geometry
const svgWidth = 640
const svgHeight = 200
const padX = 32
const padY = 22

const chart = computed(() => {
  const series = activeSeries.value
  const values = series.map((s) => s.value).filter((v): v is number => v !== null && Number.isFinite(v))
  if (!values.length) return { path: "", points: [] as Array<{ x: number; y: number; w: string; v: number | null }>, yMin: 0, yMax: 1, targetY: padY }
  const yMin = Math.min(activeSpec.value.target, ...values) * 0.92
  const yMax = Math.max(activeSpec.value.target, ...values) * 1.08
  const range = Math.max(1e-9, yMax - yMin)
  const step = series.length > 1 ? (svgWidth - padX * 2) / (series.length - 1) : 0
  const points = series.map((s, i) => {
    const x = padX + step * i
    const y = s.value === null ? padY : svgHeight - padY - ((s.value - yMin) / range) * (svgHeight - padY * 2)
    return { x, y, w: s.week, v: s.value }
  })
  const valid = points.filter((p) => p.v !== null)
  const path = valid
    .map((p, i) => `${i === 0 ? "M" : "L"}${p.x.toFixed(1)} ${p.y.toFixed(1)}`)
    .join(" ")
  const targetY = svgHeight - padY - ((activeSpec.value.target - yMin) / range) * (svgHeight - padY * 2)
  return { path, points, yMin, yMax, targetY }
})
</script>

<template>
  <section class="panel ops-panel">
    <header class="ops-panel__head">
      <div class="panel-eyebrow">
        D2: Weekly trend
        <InfoTip
          label="Weekly trend"
          content="Fleet-wide aggregates by ISO week from the Week 1…Week 5 scope rows in Regional Performance, blended with the fleet margin extract. Targets mirror the gate thresholds; the dashed horizontal line is the gate boundary. WoW arrows come from the CSV directly."
        />
      </div>
      <h2>Week-over-week performance</h2>
    </header>

    <div v-if="loading" class="ops-panel__status">Loading weekly trend…</div>
    <div v-else-if="error" class="ops-panel__status ops-panel__status--error">{{ error }}</div>
    <div v-else-if="!weeks.length" class="ops-panel__status">No weekly data. Run the operational EDA notebook.</div>

    <template v-else>
      <div class="metric-picker" role="tablist">
        <button
          v-for="m in metrics"
          :key="m.key"
          type="button"
          role="tab"
          :aria-selected="activeKey === m.key"
          class="metric-picker__btn"
          :class="{ 'metric-picker__btn--active': activeKey === m.key }"
          @click="activeKey = m.key"
        >
          {{ m.label }}
        </button>
      </div>

      <p class="metric-desc">{{ activeSpec.description }}</p>

      <div class="chart-wrap">
        <svg :viewBox="`0 0 ${svgWidth} ${svgHeight}`" preserveAspectRatio="xMidYMid meet" class="trend-svg" aria-hidden="true">
          <line
            :x1="padX"
            :x2="svgWidth - padX"
            :y1="chart.targetY"
            :y2="chart.targetY"
            class="trend-target"
          />
          <text :x="svgWidth - padX" :y="chart.targetY - 6" text-anchor="end" class="trend-target-label">
            Target {{ activeSpec.comparator === 'ge' ? '≥' : '≤' }} {{ fmtValue(activeSpec, activeSpec.target) }}
          </text>
          <path :d="chart.path" class="trend-line" />
          <g>
            <circle v-for="(p, i) in chart.points" :key="i" :cx="p.x" :cy="p.y" r="4" class="trend-dot" :data-missing="p.v === null ? 'true' : 'false'" />
            <text v-for="(p, i) in chart.points" :key="`lbl-${i}`" :x="p.x" :y="svgHeight - 4" text-anchor="middle" class="trend-xlabel">{{ p.w }}</text>
          </g>
        </svg>
      </div>

      <ul class="wow-grid">
        <li v-for="(w, i) in weeks" :key="w.week" class="wow-card">
          <div class="wow-card__week">{{ w.week }}</div>
          <div class="wow-card__value">{{ fmtValue(activeSpec, w[activeSpec.key]) }}</div>
          <div
            v-if="i > 0 && w[`${activeSpec.key}_wow`] !== null"
            class="wow-card__delta"
            :class="`wow-card__delta--${deltaTone(activeSpec, w[`${activeSpec.key}_wow`])}`"
          >
            <span aria-hidden="true">{{ (w[`${activeSpec.key}_wow`] as number) > 0 ? '▲' : (w[`${activeSpec.key}_wow`] as number) < 0 ? '▼' : '•' }}</span>
            {{ fmtDelta(activeSpec, w[`${activeSpec.key}_wow`]) }}
          </div>
          <div v-else-if="i > 0" class="wow-card__delta wow-card__delta--neutral">—</div>
        </li>
      </ul>
    </template>
  </section>
</template>

<style scoped>
.ops-panel {
  padding: 20px 22px;
}
.ops-panel__head { margin-bottom: 10px; }
.ops-panel h2 {
  margin: 4px 0 2px;
  font-size: clamp(1.1rem, 1.6vw, 1.35rem);
  letter-spacing: -0.02em;
}
.ops-panel__status {
  padding: 10px 12px;
  color: var(--muted);
  font-size: 0.9rem;
}
.ops-panel__status--error { color: var(--red); }

.metric-picker {
  display: flex;
  gap: 4px;
  padding: 4px;
  border-radius: 12px;
  background: var(--surface-2);
  border: 1px solid var(--line);
  flex-wrap: wrap;
  margin-bottom: 10px;
}
.metric-picker__btn {
  appearance: none;
  border: 0;
  background: transparent;
  padding: 6px 12px;
  border-radius: 8px;
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--muted);
  cursor: pointer;
}
.metric-picker__btn:hover { color: var(--ink); }
.metric-picker__btn--active {
  background: var(--surface);
  color: var(--blue);
  box-shadow: 0 2px 6px color-mix(in srgb, var(--blue) 16%, transparent);
}

.metric-desc {
  margin: 0 0 12px;
  color: var(--muted);
  font-size: 0.85rem;
  max-width: 56ch;
}

.chart-wrap {
  background: var(--surface-2);
  border: 1px solid var(--line);
  border-radius: 14px;
  padding: 10px;
}
.trend-svg {
  width: 100%;
  height: auto;
  display: block;
}
.trend-line {
  fill: none;
  stroke: var(--blue);
  stroke-width: 2.4;
  stroke-linecap: round;
  stroke-linejoin: round;
}
.trend-dot {
  fill: var(--blue);
  stroke: var(--surface);
  stroke-width: 2;
}
.trend-dot[data-missing="true"] {
  fill: var(--line-strong);
}
.trend-target {
  stroke: var(--maize);
  stroke-width: 1.4;
  stroke-dasharray: 4 4;
  opacity: 0.7;
}
.trend-target-label {
  font-size: 10px;
  fill: var(--maize-ink, var(--muted));
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}
.trend-xlabel {
  font-size: 10px;
  fill: var(--muted);
}

.wow-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(110px, 1fr));
  gap: 8px;
  margin: 12px 0 0;
  padding: 0;
  list-style: none;
}
.wow-card {
  padding: 10px 12px;
  border: 1px solid var(--line);
  border-radius: 12px;
  background: var(--surface-2);
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.wow-card__week {
  font-size: 0.7rem;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  font-weight: 700;
}
.wow-card__value {
  font-size: 1.05rem;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}
.wow-card__delta {
  font-size: 0.78rem;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}
.wow-card__delta--pass { color: var(--teal); }
.wow-card__delta--fail { color: var(--red); }
.wow-card__delta--neutral { color: var(--muted); }
</style>
