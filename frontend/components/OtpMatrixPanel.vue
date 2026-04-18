<script setup lang="ts">
/**
 * D4 — OTP matrix.
 *
 * Parses the nested "OTP" workbook sheet. Every non-zero cell reports an
 * on-time delivery share for a (scope=week, region, leg, day-of-week) tuple.
 * We render a week × day heat matrix with region / leg filters, so a user
 * can toggle between Grand Rapids, Lansing, fleet Total and A-/B-/overall
 * legs without leaving the tab. Cell colour is driven by the 90% gate target.
 */
type Row = {
  scope: string
  region: string
  leg: string
  day: string
  otp: number | null
}

const props = defineProps<{
  rows: Row[]
  loading?: boolean
  error?: string | null
}>()

const regions = computed(() => {
  const all = Array.from(new Set(props.rows.map((r) => r.region)))
  return all.sort((a, b) => (a === "Total" ? -1 : b === "Total" ? 1 : a.localeCompare(b)))
})
const legs = computed(() => {
  const all = Array.from(new Set(props.rows.map((r) => r.leg)))
  return all.sort((a, b) => (a === "overall" ? -1 : b === "overall" ? 1 : a.localeCompare(b)))
})
const weeks = computed(() =>
  Array.from(new Set(props.rows.filter((r) => r.scope.startsWith("Week")).map((r) => r.scope))).sort()
)
const days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

const selectedRegion = ref<string>("Total")
const selectedLeg = ref<string>("overall")

watch(regions, (r) => {
  if (r.length && !r.includes(selectedRegion.value)) selectedRegion.value = r[0]
}, { immediate: true })
watch(legs, (l) => {
  if (l.length && !l.includes(selectedLeg.value)) selectedLeg.value = l[0]
}, { immediate: true })

type CellKey = `${string}::${string}`
const cellIndex = computed(() => {
  const map = new Map<CellKey, number | null>()
  for (const row of props.rows) {
    if (row.region !== selectedRegion.value || row.leg !== selectedLeg.value) continue
    if (!days.includes(row.day)) continue
    if (!weeks.value.includes(row.scope)) continue
    map.set(`${row.scope}::${row.day}`, row.otp)
  }
  return map
})

function cellValue(week: string, day: string): number | null {
  return cellIndex.value.get(`${week}::${day}`) ?? null
}

function toneClass(v: number | null): string {
  if (v === null || v === undefined) return "otp-cell--missing"
  if (v >= 0.9) return "otp-cell--pass"
  if (v >= 0.8) return "otp-cell--warn"
  return "otp-cell--fail"
}

function fmt(v: number | null): string {
  if (v === null || v === undefined) return "—"
  return `${(v * 100).toFixed(1)}%`
}

const weeklyAverage = computed(() =>
  weeks.value.map((w) => {
    const vals = days.map((d) => cellValue(w, d)).filter((v): v is number => typeof v === "number")
    const avg = vals.length ? vals.reduce((s, x) => s + x, 0) / vals.length : null
    return { week: w, avg }
  })
)
</script>

<template>
  <section class="panel ops-panel">
    <header class="ops-panel__head">
      <div class="panel-eyebrow">
        D4: OTP matrix
        <InfoTip
          label="On-time performance matrix"
          content="Source: the OTP sheet of the Q1 workbook. Each cell is the share of legs delivered within the promised pickup window for that region/leg type/day/week combination. Target is 90% (green ≥ 90, amber 80–90, red < 80). Grand Rapids & Lansing are reported directly; other regions roll up into the fleet Total row."
        />
      </div>
      <h2>On-time performance by week &amp; day</h2>
    </header>

    <div v-if="loading" class="ops-panel__status">Loading OTP…</div>
    <div v-else-if="error" class="ops-panel__status ops-panel__status--error">{{ error }}</div>
    <div v-else-if="!rows.length" class="ops-panel__status">No OTP data.</div>

    <template v-else>
      <div class="otp-filters">
        <label>
          Region
          <select v-model="selectedRegion">
            <option v-for="r in regions" :key="r" :value="r">{{ r }}</option>
          </select>
        </label>
        <label>
          Leg
          <select v-model="selectedLeg">
            <option v-for="l in legs" :key="l" :value="l">{{ l }}</option>
          </select>
        </label>
      </div>

      <div class="otp-grid">
        <table class="otp-table" aria-label="OTP matrix">
          <thead>
            <tr>
              <th scope="col">Day</th>
              <th v-for="w in weeks" :key="w" scope="col">{{ w }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="d in days" :key="d">
              <th scope="row">{{ d }}</th>
              <td
                v-for="w in weeks"
                :key="`${w}-${d}`"
                :class="['otp-cell', toneClass(cellValue(w, d))]"
                :title="`${w} ${d}: ${fmt(cellValue(w, d))}`"
              >
                {{ fmt(cellValue(w, d)) }}
              </td>
            </tr>
            <tr class="otp-table__footer">
              <th scope="row">Avg</th>
              <td v-for="wk in weeklyAverage" :key="wk.week" :class="['otp-cell', toneClass(wk.avg)]">
                {{ fmt(wk.avg) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="otp-legend" aria-label="Legend">
        <span class="otp-legend__swatch otp-legend__swatch--pass" /> ≥ 90% (target)
        <span class="otp-legend__swatch otp-legend__swatch--warn" /> 80–90% (watch)
        <span class="otp-legend__swatch otp-legend__swatch--fail" /> &lt; 80% (alert)
        <span class="otp-legend__swatch otp-legend__swatch--missing" /> no data
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

.otp-filters {
  display: flex;
  gap: 12px;
  margin-bottom: 10px;
  flex-wrap: wrap;
}
.otp-filters label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.82rem;
  color: var(--muted);
  font-weight: 600;
}
.otp-filters select {
  padding: 4px 8px;
  border-radius: 8px;
  border: 1px solid var(--line);
  background: var(--surface-2);
  color: var(--ink);
  font: inherit;
}

.otp-grid { overflow-x: auto; }
.otp-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 4px;
  font-size: 0.86rem;
}
.otp-table thead th,
.otp-table tbody th {
  padding: 6px 10px;
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--muted);
  font-weight: 700;
  text-align: left;
  background: var(--surface-2);
  border-radius: 8px;
}
.otp-cell {
  padding: 10px 12px;
  border-radius: 8px;
  text-align: center;
  font-variant-numeric: tabular-nums;
  font-weight: 700;
  background: var(--surface-2);
  color: var(--ink);
}
.otp-cell--pass {
  background: var(--teal-soft);
  color: var(--teal);
  border: 1px solid color-mix(in srgb, var(--teal) 45%, transparent);
}
.otp-cell--warn {
  background: var(--amber-soft);
  color: var(--amber-ink, var(--amber));
  border: 1px solid color-mix(in srgb, var(--amber) 45%, transparent);
}
.otp-cell--fail {
  background: var(--red-soft);
  color: var(--red);
  border: 1px solid color-mix(in srgb, var(--red) 45%, transparent);
}
.otp-cell--missing { color: var(--muted); opacity: 0.7; }

.otp-table__footer th,
.otp-table__footer td {
  border-top: 2px solid var(--line);
  margin-top: 4px;
}

.otp-legend {
  margin-top: 10px;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px 14px;
  font-size: 0.78rem;
  color: var(--muted);
}
.otp-legend__swatch {
  display: inline-block;
  width: 12px;
  height: 12px;
  border-radius: 4px;
  margin-right: 4px;
  vertical-align: middle;
}
.otp-legend__swatch--pass { background: var(--teal); }
.otp-legend__swatch--warn { background: var(--amber); }
.otp-legend__swatch--fail { background: var(--red); }
.otp-legend__swatch--missing { background: var(--line-strong); }
</style>
