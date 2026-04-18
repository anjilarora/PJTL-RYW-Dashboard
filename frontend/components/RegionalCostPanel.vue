<script setup lang="ts">
/**
 * D10 — Regional cost estimate.
 *
 * Until RYW supplies region-tagged cost actuals we derive each region's share
 * of total cost from its vehicle count, then convert to cost per road hour
 * using the estimated road hours already in the weekly margin extract. This
 * is clearly labelled as an *estimate* so stakeholders do not mistake the
 * numbers for audited actuals; Gate 9's $50/hr target is shown alongside.
 */
type Region = {
  region: string
  vehicle_count: number | null
  cost_share_assumed: number | null
  estimated_cost: number | null
  estimated_road_hours: number | null
  estimated_cost_per_road_hour: number | null
  note: string | null
}

const props = defineProps<{
  regions: Region[]
  targetCostPerRoadHour: number
  isEstimate: boolean
  loading?: boolean
  error?: string | null
}>()

function currency(v: number | null): string {
  if (v === null || v === undefined) return "—"
  return `$${v.toLocaleString("en-US", { maximumFractionDigits: 0 })}`
}
function hours(v: number | null): string {
  if (v === null || v === undefined) return "—"
  return `${v.toLocaleString("en-US", { maximumFractionDigits: 0 })} hr`
}
function pct(v: number | null): string {
  if (v === null || v === undefined) return "—"
  return `${(v * 100).toFixed(1)}%`
}
function rate(v: number | null): string {
  if (v === null || v === undefined) return "—"
  return `$${v.toFixed(0)}`
}

function tone(rateVal: number | null): string {
  if (rateVal === null) return "neutral"
  return rateVal <= props.targetCostPerRoadHour ? "pass" : "fail"
}
</script>

<template>
  <section class="panel ops-panel">
    <header class="ops-panel__head">
      <div class="panel-eyebrow">
        D10: Regional cost estimate
        <InfoTip
          label="Regional cost estimate"
          content="RYW does not break down cost per region yet, so we allocate total fleet cost in proportion to each region's vehicle count. Road hours are the same regional road-hour estimate used in the gate scorecard. Both the allocation method and the estimate flag are surfaced in the table so downstream consumers know this is not audited."
        />
      </div>
      <h2>Estimated cost per road hour by region</h2>
      <p class="ops-panel__caption">
        Gate 9 target: <strong>≤ {{ rate(targetCostPerRoadHour) }} / road hour</strong>.
        <span v-if="isEstimate" class="estimate-chip">Estimate</span>
      </p>
    </header>

    <div v-if="loading" class="ops-panel__status">Loading regional cost…</div>
    <div v-else-if="error" class="ops-panel__status ops-panel__status--error">{{ error }}</div>
    <div v-else-if="!regions.length" class="ops-panel__status">No regional cost data.</div>

    <template v-else>
      <table class="cost-table" aria-label="Regional cost estimate">
        <thead>
          <tr>
            <th scope="col">Region</th>
            <th scope="col">Vehicles</th>
            <th scope="col">Cost share</th>
            <th scope="col">Est. cost</th>
            <th scope="col">Est. road hours</th>
            <th scope="col">Est. $/road hour</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in regions" :key="r.region">
            <th scope="row">{{ r.region }}</th>
            <td class="mono">{{ r.vehicle_count ?? "—" }}</td>
            <td class="mono">{{ pct(r.cost_share_assumed) }}</td>
            <td class="mono">{{ currency(r.estimated_cost) }}</td>
            <td class="mono">{{ hours(r.estimated_road_hours) }}</td>
            <td>
              <div class="rate-cell">
                <strong :class="`value-${tone(r.estimated_cost_per_road_hour)}`">{{ rate(r.estimated_cost_per_road_hour) }}</strong>
                <StatusPill
                  v-if="r.estimated_cost_per_road_hour !== null"
                  :label="tone(r.estimated_cost_per_road_hour) === 'pass' ? 'Within target' : 'Over target'"
                  :tone="(tone(r.estimated_cost_per_road_hour) as any)"
                  size="sm"
                />
              </div>
            </td>
          </tr>
        </tbody>
      </table>

      <p class="caveat">
        <strong>Caveat:</strong> costs are allocated proportionally to each region's vehicle count because RYW does not yet
        publish a region-tagged cost rollup. Once regional cost actuals land this panel will swap to the actuals without
        changing the layout.
      </p>
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
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
}
.ops-panel__caption strong { color: var(--ink); font-variant-numeric: tabular-nums; }
.estimate-chip {
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 999px;
  background: var(--amber-soft);
  color: var(--amber-ink, var(--amber));
  border: 1px solid color-mix(in srgb, var(--amber) 45%, transparent);
}
.ops-panel__status {
  padding: 10px 12px;
  color: var(--muted);
  font-size: 0.9rem;
}
.ops-panel__status--error { color: var(--red); }

.cost-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.88rem;
}
.cost-table th,
.cost-table td {
  padding: 8px 10px;
  border-bottom: 1px solid var(--line);
  text-align: left;
}
.cost-table thead th {
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--muted);
  font-weight: 700;
}
.cost-table tbody th {
  font-weight: 700;
  color: var(--ink);
}
.mono { font-variant-numeric: tabular-nums; }
.value-pass { color: var(--teal); }
.value-fail { color: var(--red); }
.value-neutral { color: var(--muted); }

.rate-cell {
  display: inline-flex;
  gap: 8px;
  align-items: center;
  font-variant-numeric: tabular-nums;
}

.caveat {
  margin: 10px 0 0;
  padding: 8px 12px;
  border: 1px dashed var(--line);
  border-radius: 10px;
  background: var(--surface-2);
  font-size: 0.82rem;
  color: var(--muted);
}
.caveat strong { color: var(--ink); }
</style>
