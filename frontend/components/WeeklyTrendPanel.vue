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
const chartEl = ref<HTMLElement | null>(null)
let hcLib: any = null
let hcChart: any = null

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

async function ensureHighcharts() {
  if (!import.meta.client) return
  if (!hcLib) hcLib = (await import("highcharts")).default
}

function renderChart() {
  if (!import.meta.client || !hcLib || !chartEl.value) return
  if (!props.weeks.length) return
  const spec = activeSpec.value
  const categories = props.weeks.map((w) => w.week)
  const values = props.weeks.map((w) => w[spec.key] as number | null)
  const wow = props.weeks.map((w) => w[`${spec.key}_wow` as keyof Week] as number | null)
  const pct = spec.format === "pct"
  const money = spec.format === "currency"
  const ratio = spec.format === "ratio"
  if (hcChart) hcChart.destroy()
  hcChart = hcLib.chart(chartEl.value, {
    chart: {
      type: "line",
      backgroundColor: "transparent",
      spacingTop: 18,
      spacingRight: 18,
      spacingLeft: 8,
      spacingBottom: 8,
      animation: { duration: 260 }
    },
    title: { text: undefined },
    credits: { enabled: false },
    legend: { enabled: true, itemStyle: { color: "#98a4b7", fontSize: "11px" } },
    xAxis: {
      categories,
      lineColor: "rgba(152,164,183,0.25)",
      tickColor: "rgba(152,164,183,0.25)",
      labels: { style: { color: "#98a4b7", fontSize: "11px" } }
    },
    yAxis: [{
      title: { text: undefined },
      gridLineColor: "rgba(152,164,183,0.16)",
      labels: {
        style: { color: "#98a4b7", fontSize: "11px" },
        formatter: function (this: any) {
          const v = Number(this.value)
          if (pct) return `${(v * 100).toFixed(0)}%`
          if (money) return `$${v.toFixed(0)}`
          if (ratio) return v.toFixed(2)
          return String(v)
        }
      },
      plotLines: [{
        value: spec.target,
        color: "rgba(255,203,5,0.9)",
        width: 1.4,
        dashStyle: "Dash",
        zIndex: 5,
        label: {
          text: `Target ${spec.comparator === "ge" ? "≥" : "≤"} ${fmtValue(spec, spec.target)}`,
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
        const week = categories[idx] ?? ""
        const val = values[idx]
        const d = wow[idx]
        const vText = fmtValue(spec, val)
        const dText = d == null ? "—" : fmtDelta(spec, d)
        return `<b>${week}</b><br/>${spec.label}: <b>${vText}</b><br/>WoW: <b>${dText}</b>`
      }
    },
    plotOptions: {
      series: {
        animation: { duration: 250 },
        marker: { enabled: true, radius: 4, lineWidth: 1.5, lineColor: "#121720" }
      }
    },
    series: [
      {
        type: "line",
        name: spec.label,
        color: "#5b9bff",
        data: values.map((v) => (v == null ? null : Number(v)))
      },
      {
        type: "column",
        name: "WoW delta",
        yAxis: 0,
        color: "rgba(53,211,156,0.42)",
        data: wow.map((v) => (v == null ? null : Number(v))),
        visible: false
      }
    ]
  })
}

onMounted(async () => {
  await ensureHighcharts()
  renderChart()
})

watch(
  [() => props.weeks, activeKey],
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
        D2: Weekly trend
        <InfoTip
          label="Weekly trend"
          content="Fleet-wide aggregates by ISO week from the Week 1…Week 5 scope rows in Regional Performance, blended with the fleet margin extract. Targets mirror the gate thresholds; the dashed horizontal line is the gate boundary. WoW arrows come from the CSV directly."
        />
      </div>
      <h2>Week-over-week performance</h2>
    </header>

    <div v-if="loading" class="ops-panel__status ops-panel__status--skeleton" aria-live="polite">
      <div class="skeleton skeleton-line" />
      <div class="skeleton skeleton-chart" />
    </div>
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
        <div ref="chartEl" class="trend-chart" />
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
.ops-panel__status--skeleton {
  display: grid;
  gap: 8px;
}
.skeleton-line {
  height: 12px;
  width: 56%;
}
.skeleton-chart {
  height: 210px;
}

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
  transition: border-color 160ms ease, box-shadow 160ms ease;
}
.chart-wrap:hover {
  border-color: color-mix(in srgb, var(--blue) 28%, var(--line));
  box-shadow: 0 4px 14px color-mix(in srgb, var(--blue) 16%, transparent);
}
.trend-chart {
  width: 100%;
  min-height: 260px;
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
