<script setup lang="ts">
/**
 * D1 — Regional gate scorecard.
 *
 * Reads ``GET /api/v1/dashboard/fleet-scorecard`` and renders a region-by-gate
 * grid. Each region is a collapsible card showing every gate's target, actual,
 * and pass / fail verdict. Target comparators are rendered as glyphs (>=, <=)
 * and status pills reuse the shared pass/fail/provisional tokens so the colour
 * language matches the Launch Readiness carousel.
 */
type Gate = {
  gate: string
  label: string
  target: number | null
  comparator: string | null
  value: number | null
  pass: boolean | null
  detail: string | null
}

type Region = {
  region: string
  gates: Gate[]
}

const props = defineProps<{
  regions: Region[]
  loading?: boolean
  error?: string | null
}>()

const openRegion = ref<string | null>(null)

watch(
  () => props.regions,
  (rows) => {
    if (!openRegion.value && rows?.length) openRegion.value = rows[0].region
  },
  { immediate: true }
)

function toggle(region: string) {
  openRegion.value = openRegion.value === region ? null : region
}

function fmt(g: Gate): string {
  if (g.value === null || g.value === undefined) return "—"
  const v = g.value
  if (g.gate.includes("utilization") || g.gate.includes("pool") || g.gate.includes("otp")) {
    return `${(v * 100).toFixed(1)}%`
  }
  if (g.gate.includes("rev_per_kentleg")) return `$${v.toFixed(1)}`
  if (g.gate.includes("acuity") || g.gate.includes("nonbillable") || g.gate.includes("payer"))
    return `${(v * 100).toFixed(1)}%`
  if (g.gate.includes("road_time")) return `${v.toFixed(2)} hr`
  if (g.gate.includes("cost_per_road_hour")) return `$${v.toFixed(1)}`
  return v.toFixed(2)
}

function fmtTarget(g: Gate): string {
  if (g.target === null || g.target === undefined) return ""
  const t = g.target
  const c = g.comparator === "le" ? "≤" : "≥"
  if (g.gate.includes("utilization") || g.gate.includes("pool"))
    return `${c} ${(t * 100).toFixed(0)}%`
  if (g.gate.includes("rev_per_kentleg")) return `${c} $${t.toFixed(0)}`
  if (g.gate.includes("acuity") || g.gate.includes("nonbillable") || g.gate.includes("payer"))
    return `${c} ${(t * 100).toFixed(0)}%`
  if (g.gate.includes("road_time")) return `${c} ${t.toFixed(1)} hr`
  if (g.gate.includes("cost_per_road_hour")) return `${c} $${t.toFixed(0)}`
  return `${c} ${t}`
}

function regionSummary(r: Region): { pass: number; fail: number; missing: number } {
  let pass = 0
  let fail = 0
  let missing = 0
  for (const g of r.gates) {
    if (g.pass === true) pass += 1
    else if (g.pass === false) fail += 1
    else missing += 1
  }
  return { pass, fail, missing }
}
</script>

<template>
  <section class="panel ops-panel">
    <header class="ops-panel__head">
      <div class="panel-eyebrow">
        D1: Regional readiness scorecard
        <InfoTip
          label="Regional scorecard"
          content="For each of the six regions we compute the nine launch-readiness gates from the Q1 Regional Performance sheet plus base contract volume. Targets mirror the Go/No-Go thresholds in code/config/pjtl_kpis_and_formulas.json. Pass ▸ green, Fail ▸ red, Missing data ▸ grey."
        />
      </div>
      <h2>Fleet readiness by region</h2>
      <p class="ops-panel__caption">
        Click a region to expand the full nine-gate detail. Counts below each header show pass / fail / missing data.
      </p>
    </header>

    <div v-if="loading" class="ops-panel__status">Loading regional scorecard…</div>
    <div v-else-if="error" class="ops-panel__status ops-panel__status--error">{{ error }}</div>
    <div v-else-if="!regions.length" class="ops-panel__status">
      No regional data found. Run <code>python code/inference_engine/scripts/operational_eda.py</code> to regenerate.
    </div>

    <ul v-else class="region-list">
      <li v-for="r in regions" :key="r.region" class="region-card">
        <button
          type="button"
          class="region-card__head"
          :aria-expanded="openRegion === r.region"
          @click="toggle(r.region)"
        >
          <span class="region-card__name">{{ r.region }}</span>
          <span class="region-card__summary">
            <span class="summary-chip summary-chip--pass">{{ regionSummary(r).pass }} pass</span>
            <span class="summary-chip summary-chip--fail">{{ regionSummary(r).fail }} fail</span>
            <span v-if="regionSummary(r).missing" class="summary-chip summary-chip--missing">{{ regionSummary(r).missing }} missing</span>
          </span>
          <span class="region-card__chevron" :class="{ 'region-card__chevron--open': openRegion === r.region }" aria-hidden="true">▾</span>
        </button>

        <table v-show="openRegion === r.region" class="gate-table" aria-label="Gate detail">
          <thead>
            <tr>
              <th scope="col">Gate</th>
              <th scope="col">Target</th>
              <th scope="col">Actual</th>
              <th scope="col">Status</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="g in r.gates" :key="g.gate" :class="{ 'gate-table__row--missing': g.pass === null }">
              <th scope="row">{{ g.label }}</th>
              <td class="gate-table__target">{{ fmtTarget(g) }}</td>
              <td class="gate-table__value">{{ fmt(g) }}</td>
              <td>
                <StatusPill
                  v-if="g.pass === true"
                  label="Pass"
                  tone="pass"
                  size="sm"
                />
                <StatusPill
                  v-else-if="g.pass === false"
                  label="Fail"
                  tone="fail"
                  size="sm"
                />
                <StatusPill v-else label="No data" tone="neutral" size="sm" />
              </td>
            </tr>
          </tbody>
        </table>
      </li>
    </ul>
  </section>
</template>

<style scoped>
.ops-panel {
  padding: 20px 22px;
  margin-top: 0;
}
.ops-panel__head {
  margin-bottom: 10px;
}
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
.ops-panel__status--error {
  color: var(--red);
}

.region-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.region-card {
  border: 1px solid var(--line);
  border-radius: 14px;
  background: var(--surface-2);
  overflow: hidden;
}
.region-card__head {
  appearance: none;
  border: 0;
  background: transparent;
  width: 100%;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  cursor: pointer;
  text-align: left;
  color: var(--ink);
}
.region-card__head:hover {
  background: color-mix(in srgb, var(--blue) 6%, transparent);
}
.region-card__name {
  font-weight: 700;
  font-size: 0.98rem;
  flex: 1 1 auto;
}
.region-card__summary {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}
.summary-chip {
  font-size: 0.72rem;
  font-weight: 700;
  padding: 3px 8px;
  border-radius: 999px;
  letter-spacing: 0.03em;
  text-transform: uppercase;
  border: 1px solid transparent;
}
.summary-chip--pass {
  background: var(--teal-soft);
  color: var(--teal);
  border-color: color-mix(in srgb, var(--teal) 45%, transparent);
}
.summary-chip--fail {
  background: var(--red-soft);
  color: var(--red);
  border-color: color-mix(in srgb, var(--red) 45%, transparent);
}
.summary-chip--missing {
  background: var(--surface);
  color: var(--muted);
  border-color: var(--line);
}
.region-card__chevron {
  color: var(--muted);
  transition: transform 160ms ease;
  font-size: 0.9rem;
}
.region-card__chevron--open {
  transform: rotate(180deg);
}

.gate-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.88rem;
  background: var(--surface);
}
.gate-table th,
.gate-table td {
  padding: 8px 14px;
  border-top: 1px solid var(--line);
  text-align: left;
}
.gate-table thead th {
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--muted);
  font-weight: 700;
}
.gate-table tbody th {
  font-weight: 600;
  color: var(--ink);
}
.gate-table__target {
  font-variant-numeric: tabular-nums;
  color: var(--muted);
}
.gate-table__value {
  font-variant-numeric: tabular-nums;
  font-weight: 600;
}
.gate-table__row--missing th,
.gate-table__row--missing td {
  color: var(--muted);
}
</style>
