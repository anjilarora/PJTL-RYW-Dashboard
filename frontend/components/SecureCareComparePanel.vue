<script setup lang="ts">
/**
 * D9 — SecureCare vs fleet compare.
 *
 * Reads the ``cost_margin_trend.csv`` grouped by stream (Fleet vs SecureCare)
 * and week. Each stream gets a summary card with total revenue, total cost,
 * net margin, margin %, and a week-by-week breakdown. A small margin sparkline
 * makes it obvious whether SecureCare's margin trajectory is converging with
 * or diverging from the base fleet.
 */
type Week = {
  week: string
  total_revenue: number | null
  total_cost: number | null
  profit_margin: number | null
}
type Stream = {
  total_revenue: number
  total_cost: number
  net_margin: number
  margin_pct: number | null
  weeks: Week[]
}

const props = defineProps<{
  streams: Record<string, Stream>
  loading?: boolean
  error?: string | null
}>()

const order = ["Fleet", "SecureCare"]
const ordered = computed(() =>
  Object.entries(props.streams).sort((a, b) => order.indexOf(a[0]) - order.indexOf(b[0]))
)

function currency(v: number | null): string {
  if (v === null || v === undefined) return "—"
  return `$${v.toLocaleString("en-US", { maximumFractionDigits: 0 })}`
}
function pct(v: number | null): string {
  if (v === null || v === undefined) return "—"
  return `${(v * 100).toFixed(1)}%`
}

function sparkPath(stream: Stream): string {
  if (!stream.weeks.length) return ""
  const vals = stream.weeks.map((w) => w.profit_margin ?? 0)
  const min = Math.min(-0.1, ...vals)
  const max = Math.max(0.1, ...vals)
  const range = max - min || 1
  const w = 180
  const h = 44
  const step = vals.length > 1 ? w / (vals.length - 1) : 0
  return vals
    .map((v, i) => {
      const x = i * step
      const y = h - ((v - min) / range) * h
      return `${i === 0 ? "M" : "L"}${x.toFixed(1)} ${y.toFixed(1)}`
    })
    .join(" ")
}

function zeroLineY(stream: Stream): number {
  const vals = stream.weeks.map((w) => w.profit_margin ?? 0)
  const min = Math.min(-0.1, ...vals)
  const max = Math.max(0.1, ...vals)
  const range = max - min || 1
  const h = 44
  return h - ((0 - min) / range) * h
}
</script>

<template>
  <section class="panel ops-panel">
    <header class="ops-panel__head">
      <div class="panel-eyebrow">
        D9: SecureCare vs Fleet
        <InfoTip
          label="SecureCare vs Fleet"
          content="Side-by-side weekly revenue, cost, and margin for the base Fleet stream and the SecureCare stream (the separate A-leg + wait-time programme the operator runs for a VA-type customer). Margins are (revenue − cost) / revenue for each stream and week. The sparkline shows the 5-week margin trajectory; the horizontal line is the 0% breakeven reference."
        />
      </div>
      <h2>Fleet vs SecureCare margins</h2>
    </header>

    <div v-if="loading" class="ops-panel__status">Loading margin comparison…</div>
    <div v-else-if="error" class="ops-panel__status ops-panel__status--error">{{ error }}</div>
    <div v-else-if="!ordered.length" class="ops-panel__status">No stream data.</div>

    <template v-else>
      <div class="stream-grid">
        <article v-for="[name, s] in ordered" :key="name" class="stream-card">
          <header class="stream-card__head">
            <h3>{{ name }}</h3>
            <span :class="`stream-card__margin stream-card__margin--${s.margin_pct !== null && s.margin_pct >= 0 ? 'pass' : 'fail'}`">
              {{ pct(s.margin_pct) }} margin
            </span>
          </header>

          <dl class="stream-stats">
            <div><dt>Total revenue</dt><dd>{{ currency(s.total_revenue) }}</dd></div>
            <div><dt>Total cost</dt><dd>{{ currency(s.total_cost) }}</dd></div>
            <div>
              <dt>Net margin</dt>
              <dd :class="`value-${s.net_margin >= 0 ? 'pass' : 'fail'}`">{{ currency(s.net_margin) }}</dd>
            </div>
          </dl>

          <svg viewBox="0 0 180 44" class="stream-spark" aria-hidden="true">
            <line x1="0" :y1="zeroLineY(s)" x2="180" :y2="zeroLineY(s)" class="stream-spark__zero" />
            <path :d="sparkPath(s)" class="stream-spark__line" />
          </svg>

          <table class="stream-weeks">
            <thead>
              <tr>
                <th scope="col">Week</th>
                <th scope="col">Revenue</th>
                <th scope="col">Cost</th>
                <th scope="col">Margin</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="w in s.weeks" :key="w.week">
                <th scope="row">{{ w.week }}</th>
                <td class="mono">{{ currency(w.total_revenue) }}</td>
                <td class="mono">{{ currency(w.total_cost) }}</td>
                <td class="mono" :class="`value-${(w.profit_margin ?? 0) >= 0 ? 'pass' : 'fail'}`">{{ pct(w.profit_margin) }}</td>
              </tr>
            </tbody>
          </table>
        </article>
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

.stream-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 14px;
}
.stream-card {
  padding: 14px 16px;
  border: 1px solid var(--line);
  border-radius: 14px;
  background: var(--surface-2);
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.stream-card__head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 10px;
}
.stream-card__head h3 {
  margin: 0;
  font-size: 1.05rem;
  letter-spacing: -0.02em;
}
.stream-card__margin {
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}
.stream-card__margin--pass { color: var(--teal); }
.stream-card__margin--fail { color: var(--red); }

.stream-stats {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
  margin: 0;
}
.stream-stats dt {
  font-size: 0.7rem;
  color: var(--muted);
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}
.stream-stats dd {
  margin: 2px 0 0;
  font-variant-numeric: tabular-nums;
  font-weight: 700;
  font-size: 0.95rem;
}
.value-pass { color: var(--teal); }
.value-fail { color: var(--red); }

.stream-spark {
  width: 100%;
  height: 44px;
  background: var(--surface);
  border-radius: 8px;
  border: 1px solid var(--line);
}
.stream-spark__line {
  fill: none;
  stroke: var(--blue);
  stroke-width: 2.2;
  stroke-linecap: round;
  stroke-linejoin: round;
}
.stream-spark__zero {
  stroke: var(--line-strong);
  stroke-dasharray: 3 3;
  stroke-width: 1.2;
}

.stream-weeks {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.82rem;
}
.stream-weeks th,
.stream-weeks td {
  padding: 4px 8px;
  text-align: left;
  border-top: 1px solid var(--line);
}
.stream-weeks thead th {
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--muted);
  font-weight: 700;
}
.mono { font-variant-numeric: tabular-nums; font-weight: 600; }
</style>
