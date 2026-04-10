<script setup lang="ts">
type Readiness = {
  projectedWeeklyRevenue: number
  projectedMarginPct: number
  projectedRevenuePerKentLeg: number
  targetRevenuePerKentLeg: number
  targetMarginPct: number
  projectedRoadHoursPerVehicleDay: number
  projectedHigherAcuitySharePct: number
}
type Prospective = {
  completedTripsPerWeek: number
  qualitySharePct: number
  topProgramVolumeSharePct: number
  projectedCost: number
}

const props = withDefaults(
  defineProps<{
    readiness: Readiness
    prospective: Prospective
    source?: "baseline" | "evaluation" | "upload"
    periodLabel?: string
    asOf?: string
  }>(),
  {
    source: "baseline",
    periodLabel: "",
    asOf: ""
  }
)

const currency = (n: number) =>
  n.toLocaleString("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 })

const weekTag = computed(() => {
  if (props.periodLabel) return props.periodLabel
  if (props.source === "upload") return "Per-week average · uploaded workbook"
  if (props.source === "evaluation") return "Per-week projection · latest evaluation"
  return "Per-week average · 5-week baseline (Dec 29 2025 – Jan 31 2026)"
})

const weekTipContent = computed(() => {
  if (props.source === "upload") {
    return "These values are the per-week average extracted from the workbook you uploaded, combined with the intake projection. Each KPI is a single weekly figure, not a specific calendar week."
  }
  if (props.source === "evaluation") {
    return "These values are the per-week projection from the most recent readiness evaluation run. They represent the steady-state weekly figure the engine scored, not any one calendar week in your history."
  }
  return "These values are the per-week average of the bundled January 2026 reference dataset (Dec 29 2025 – Jan 31 2026, five operating weeks), blended with the prospective intake. Each KPI is one steady-state weekly figure, not a specific calendar week."
})
</script>

<template>
  <article class="panel kpi-snapshot">
    <header class="kpi-snapshot__head">
      <div class="kpi-snapshot__title">
        <div class="panel-eyebrow">
          Operating KPIs
          <InfoTip
            label="Which week is this?"
            :content="weekTipContent"
          />
        </div>
        <h2>Per-week operating snapshot</h2>
      </div>
      <div class="kpi-snapshot__period" :title="weekTag">
        <svg viewBox="0 0 24 24" width="12" height="12" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <rect x="3" y="5" width="18" height="16" rx="2" />
          <path d="M3 9h18" />
          <path d="M8 3v4" />
          <path d="M16 3v4" />
        </svg>
        <span>{{ weekTag }}</span>
      </div>
    </header>

    <div class="kpi-snapshot__grid">
      <!-- Ring charts for percentage-style KPIs -->
      <RingStat
        label="Projected margin"
        :value="readiness.projectedMarginPct"
        :max="Math.max(readiness.targetMarginPct, 1)"
        :threshold="readiness.targetMarginPct"
        :threshold-label="`Target ≥ ${readiness.targetMarginPct.toFixed(0)}%`"
      />
      <RingStat
        label="Quality-volume share"
        :value="prospective.qualitySharePct"
        :max="100"
      />
      <RingStat
        label="Higher-acuity share"
        :value="readiness.projectedHigherAcuitySharePct"
        :max="100"
        :threshold="5"
        threshold-label="Target ≥ 5%"
      />
      <RingStat
        label="Top-program concentration"
        :value="prospective.topProgramVolumeSharePct"
        :max="100"
        :threshold="20"
        tone="fail"
        threshold-label="Cap ≤ 20%"
      />

      <!-- Bar charts for numeric KPIs -->
      <BarStat
        label="Revenue / Kent-Leg"
        :value="readiness.projectedRevenuePerKentLeg"
        :max="Math.max(readiness.targetRevenuePerKentLeg, readiness.projectedRevenuePerKentLeg)"
        :formatted="`$${readiness.projectedRevenuePerKentLeg.toFixed(2)}`"
        :threshold="readiness.targetRevenuePerKentLeg"
        :threshold-label="`Target ≥ $${readiness.targetRevenuePerKentLeg.toFixed(0)}`"
      />
      <BarStat
        label="Road hrs / vehicle / day"
        :value="readiness.projectedRoadHoursPerVehicleDay"
        :max="12"
        :formatted="readiness.projectedRoadHoursPerVehicleDay.toFixed(2)"
        :threshold="9"
        threshold-label="Target ≥ 9.0"
      />
      <BarStat
        label="Weekly revenue"
        :value="readiness.projectedWeeklyRevenue"
        :max="Math.max(readiness.projectedWeeklyRevenue, prospective.projectedCost) * 1.1"
        :formatted="currency(readiness.projectedWeeklyRevenue)"
        tone="neutral"
      />
      <BarStat
        label="Weekly cost"
        :value="prospective.projectedCost"
        :max="Math.max(readiness.projectedWeeklyRevenue, prospective.projectedCost) * 1.1"
        :formatted="currency(prospective.projectedCost)"
        :threshold="readiness.projectedWeeklyRevenue"
        threshold-comparator="lte"
      />
      <BarStat
        label="Completed trips / week"
        :value="prospective.completedTripsPerWeek"
        :max="Math.max(prospective.completedTripsPerWeek * 1.4, 100)"
        :formatted="String(prospective.completedTripsPerWeek)"
        tone="neutral"
      />
    </div>
  </article>
</template>

<style scoped>
.kpi-snapshot {
  padding: 18px 22px;
}
.kpi-snapshot__head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 14px;
  margin-bottom: 14px;
  flex-wrap: wrap;
}
.kpi-snapshot__title h2 {
  margin: 0;
  font-size: clamp(1.05rem, 1.6vw, 1.35rem);
  letter-spacing: -0.03em;
}
.kpi-snapshot__period {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 10px;
  border-radius: 999px;
  background: var(--surface-2);
  border: 1px solid var(--line);
  color: var(--muted);
  font-size: 0.76rem;
  font-weight: 600;
  letter-spacing: 0.01em;
  max-width: 100%;
}
.kpi-snapshot__period svg {
  color: var(--maize-ink);
  flex-shrink: 0;
}
.kpi-snapshot__period span {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.kpi-snapshot__grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 12px;
}
@media (max-width: 720px) {
  .kpi-snapshot__grid {
    grid-template-columns: 1fr 1fr;
  }
}
</style>
