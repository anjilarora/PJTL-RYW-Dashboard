<script setup lang="ts">
/**
 * D6 — Hourly demand / idle windows.
 *
 * Flattens ``hourly_demand_idle.csv`` into a day × hour matrix for either the
 * ``requested`` (total trip requests) or ``completed`` (billable completions)
 * series. Cells scale from the lowest-to-highest value in the active metric;
 * business-hour windows (Mon–Fri 08:00–18:00) that are zero are highlighted
 * as idle-yet-staffed risk cells.
 */
type Row = {
  day: string
  hour: string
  value: number | null
  metric: string
  is_idle_business: boolean | null
}

const props = defineProps<{
  rows: Row[]
  idleWindows: Row[]
  loading?: boolean
  error?: string | null
}>()

const metrics = ["requested", "completed"] as const
type Metric = typeof metrics[number]

const activeMetric = ref<Metric>("requested")

const days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
const hours = computed(() => {
  const set = new Set<string>()
  for (const r of props.rows) set.add(r.hour)
  return Array.from(set).sort()
})

const matrix = computed(() => {
  const map = new Map<string, number | null>()
  let max = 0
  for (const r of props.rows) {
    if (r.metric !== activeMetric.value) continue
    map.set(`${r.day}::${r.hour}`, r.value)
    if ((r.value ?? 0) > max) max = r.value ?? 0
  }
  return { map, max }
})

function cellValue(day: string, hour: string): number | null {
  return matrix.value.map.get(`${day}::${hour}`) ?? null
}
function isBusinessIdle(day: string, hour: string): boolean {
  const v = cellValue(day, hour)
  if (v !== 0 && v !== null) return false
  const hh = Number(hour.slice(0, 2))
  const weekday = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"].includes(day)
  return weekday && hh >= 8 && hh < 18
}
function shade(day: string, hour: string): string {
  const v = cellValue(day, hour) ?? 0
  if (matrix.value.max <= 0) return "transparent"
  const alpha = Math.max(0, Math.min(1, v / matrix.value.max)) * 0.9 + 0.05
  if (isBusinessIdle(day, hour)) return "color-mix(in srgb, var(--amber) 40%, var(--surface-2))"
  return `color-mix(in srgb, var(--blue) ${Math.round(alpha * 100)}%, var(--surface-2))`
}
function fmt(v: number | null): string {
  if (v === null || v === undefined) return "—"
  return v.toLocaleString("en-US", { maximumFractionDigits: 0 })
}

const totals = computed(() => {
  const byDay = new Map<string, number>()
  let total = 0
  for (const r of props.rows) {
    if (r.metric !== activeMetric.value) continue
    byDay.set(r.day, (byDay.get(r.day) ?? 0) + (r.value ?? 0))
    total += r.value ?? 0
  }
  return { byDay, total }
})
</script>

<template>
  <section class="panel ops-panel">
    <header class="ops-panel__head">
      <div class="panel-eyebrow">
        D6: Hourly demand
        <InfoTip
          label="Hourly demand heat map"
          content="Breaks demand down by day of week and hour of day. Switch between requested trips (total demand) and completed trips (paid legs). Amber cells flag weekday business hours (Monday–Friday, 8am–6pm) with zero completed trips: windows where crews were staffed but no rides ran."
        />
      </div>
      <h2>Demand &amp; idle windows</h2>
    </header>

    <div v-if="loading" class="ops-panel__status">Loading hourly demand…</div>
    <div v-else-if="error" class="ops-panel__status ops-panel__status--error">{{ error }}</div>
    <div v-else-if="!rows.length" class="ops-panel__status">No hourly demand data.</div>

    <template v-else>
      <div class="heat-toolbar">
        <div class="heat-toolbar__metric" role="tablist">
          <button
            v-for="m in metrics"
            :key="m"
            type="button"
            role="tab"
            :aria-selected="activeMetric === m"
            :class="['heat-toolbar__btn', { 'heat-toolbar__btn--active': activeMetric === m }]"
            @click="activeMetric = m"
          >
            {{ m === "requested" ? "Trips requested" : "Trips completed" }}
          </button>
        </div>
        <div class="heat-toolbar__summary">
          Total {{ activeMetric }}: <strong>{{ totals.total.toLocaleString("en-US", { maximumFractionDigits: 0 }) }}</strong>
        </div>
      </div>

      <div class="heat-wrap">
        <table class="heat-table" aria-label="Hourly demand heatmap">
          <thead>
            <tr>
              <th scope="col">Hour</th>
              <th v-for="d in days" :key="d" scope="col">{{ d.slice(0, 3) }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="h in hours" :key="h">
              <th scope="row">{{ h.slice(0, 5) }}</th>
              <td
                v-for="d in days"
                :key="`${d}-${h}`"
                class="heat-cell"
                :style="{ background: shade(d, h) }"
                :title="`${d} ${h.slice(0, 5)} · ${activeMetric}: ${fmt(cellValue(d, h))}`"
              >
                {{ fmt(cellValue(d, h)) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-if="idleWindows.length" class="idle-list">
        <div class="panel-eyebrow">Idle business-hour windows ({{ idleWindows.length }})</div>
        <ul>
          <li v-for="(w, i) in idleWindows.slice(0, 12)" :key="i">
            {{ w.day }} {{ w.hour.slice(0, 5) }}: zero completed trips
          </li>
          <li v-if="idleWindows.length > 12" class="muted">
            …and {{ idleWindows.length - 12 }} more in the heat map above
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
.ops-panel__status {
  padding: 10px 12px;
  color: var(--muted);
  font-size: 0.9rem;
}
.ops-panel__status--error { color: var(--red); }

.heat-toolbar {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 10px;
  align-items: center;
}
.heat-toolbar__metric {
  display: inline-flex;
  gap: 4px;
  padding: 4px;
  border-radius: 10px;
  background: var(--surface-2);
  border: 1px solid var(--line);
}
.heat-toolbar__btn {
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
.heat-toolbar__btn--active {
  background: var(--surface);
  color: var(--blue);
}
.heat-toolbar__summary {
  font-size: 0.82rem;
  color: var(--muted);
}
.heat-toolbar__summary strong {
  color: var(--ink);
  font-variant-numeric: tabular-nums;
}

.heat-wrap { overflow-x: auto; }
.heat-table {
  border-collapse: separate;
  border-spacing: 2px;
  font-size: 0.72rem;
  font-variant-numeric: tabular-nums;
}
.heat-table thead th,
.heat-table tbody th {
  padding: 4px 8px;
  font-size: 0.7rem;
  color: var(--muted);
  font-weight: 700;
  background: var(--surface-2);
  border-radius: 6px;
  text-align: left;
}
.heat-cell {
  min-width: 36px;
  text-align: center;
  padding: 6px 4px;
  border-radius: 6px;
  color: var(--ink);
}

.idle-list {
  margin-top: 14px;
  padding: 10px 12px;
  border: 1px solid color-mix(in srgb, var(--amber) 40%, var(--line));
  border-radius: 12px;
  background: color-mix(in srgb, var(--amber-soft) 40%, var(--surface-2));
}
.idle-list ul {
  margin: 6px 0 0;
  padding-left: 1.2rem;
  font-size: 0.84rem;
  color: var(--ink);
}
.idle-list li.muted { color: var(--muted); }
</style>
