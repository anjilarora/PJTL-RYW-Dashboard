<script setup lang="ts">
/**
 * D7 — Cancellation patterns.
 *
 * Aggregates ``cancellation_patterns.csv`` into four top-N lists (by reason,
 * mode, day, payer) plus a detail table of the loudest combinations. The
 * backend sorts ``rows`` descending by count already; this panel is a pure
 * renderer.
 */
type Combo = {
  order_status: string | null
  reason: string | null
  payer_id: string | null
  order_mode: string | null
  day: string | null
  count: number
}
type TopN = { key: string; count: number }

const props = defineProps<{
  rows: Combo[]
  byReason: TopN[]
  byMode: TopN[]
  byDay: TopN[]
  byPayer: TopN[]
  total: number
  loading?: boolean
  error?: string | null
}>()

function normalizedShare(list: TopN[]): TopN[] {
  const total = list.reduce((s, t) => s + t.count, 0)
  if (!total) return list
  return list.map((t) => ({ ...t, count: t.count, share: t.count / total } as TopN & { share: number }))
}

const topReasons = computed(() => normalizedShare(props.byReason) as Array<TopN & { share?: number }>)
const topModes = computed(() => normalizedShare(props.byMode) as Array<TopN & { share?: number }>)
const topDays = computed(() => normalizedShare(props.byDay) as Array<TopN & { share?: number }>)
const topPayers = computed(() => normalizedShare(props.byPayer) as Array<TopN & { share?: number }>)

function pct(v: number | undefined): string {
  if (v === undefined || v === null) return ""
  return `${(v * 100).toFixed(1)}%`
}
</script>

<template>
  <section class="panel ops-panel">
    <header class="ops-panel__head">
      <div class="panel-eyebrow">
        D7: Cancellation analyzer
        <InfoTip
          label="Cancellation analyzer"
          content="Groups every cancelled or turned-down order in contract_volume_base.csv by reason, mode, day-of-week, and payer. Use it to pinpoint which reason codes or payers generate the most abandoned legs; the detail rows below are the loudest (reason × payer × mode × day) combinations."
        />
      </div>
      <h2>Cancellations breakdown</h2>
      <p class="ops-panel__caption">
        <strong>{{ total.toLocaleString("en-US") }}</strong> cancellations tagged across Q1 2025 (5 operating weeks).
      </p>
    </header>

    <div v-if="loading" class="ops-panel__status">Loading cancellations…</div>
    <div v-else-if="error" class="ops-panel__status ops-panel__status--error">{{ error }}</div>
    <div v-else-if="!rows.length" class="ops-panel__status">No cancellation data.</div>

    <template v-else>
      <div class="cancel-grid">
        <div class="cancel-block">
          <div class="cancel-block__title">Top reasons</div>
          <ul>
            <li v-for="t in topReasons" :key="t.key">
              <span class="cancel-row__key">{{ t.key || "Unknown" }}</span>
              <span class="cancel-row__count">{{ t.count.toLocaleString("en-US") }}</span>
              <span class="cancel-row__share">{{ pct(t.share) }}</span>
            </li>
          </ul>
        </div>
        <div class="cancel-block">
          <div class="cancel-block__title">Top modes</div>
          <ul>
            <li v-for="t in topModes" :key="t.key">
              <span class="cancel-row__key">{{ t.key || "Unknown" }}</span>
              <span class="cancel-row__count">{{ t.count.toLocaleString("en-US") }}</span>
              <span class="cancel-row__share">{{ pct(t.share) }}</span>
            </li>
          </ul>
        </div>
        <div class="cancel-block">
          <div class="cancel-block__title">Top days</div>
          <ul>
            <li v-for="t in topDays" :key="t.key">
              <span class="cancel-row__key">{{ t.key || "Unknown" }}</span>
              <span class="cancel-row__count">{{ t.count.toLocaleString("en-US") }}</span>
              <span class="cancel-row__share">{{ pct(t.share) }}</span>
            </li>
          </ul>
        </div>
        <div class="cancel-block">
          <div class="cancel-block__title">Top payers</div>
          <ul>
            <li v-for="t in topPayers" :key="t.key">
              <span class="cancel-row__key">{{ t.key || "Unknown" }}</span>
              <span class="cancel-row__count">{{ t.count.toLocaleString("en-US") }}</span>
              <span class="cancel-row__share">{{ pct(t.share) }}</span>
            </li>
          </ul>
        </div>
      </div>

      <details class="cancel-detail">
        <summary>Loudest combinations ({{ rows.length }})</summary>
        <table class="cancel-table" aria-label="Cancellation detail">
          <thead>
            <tr>
              <th scope="col">Status</th>
              <th scope="col">Reason</th>
              <th scope="col">Payer</th>
              <th scope="col">Mode</th>
              <th scope="col">Day</th>
              <th scope="col">Count</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(r, i) in rows" :key="i">
              <td>{{ r.order_status ?? "—" }}</td>
              <td>{{ r.reason ?? "—" }}</td>
              <td>{{ r.payer_id ?? "—" }}</td>
              <td>{{ r.order_mode ?? "—" }}</td>
              <td>{{ r.day ?? "—" }}</td>
              <td class="mono">{{ r.count.toLocaleString("en-US") }}</td>
            </tr>
          </tbody>
        </table>
      </details>
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
.ops-panel__caption strong { color: var(--ink); font-variant-numeric: tabular-nums; }
.ops-panel__status {
  padding: 10px 12px;
  color: var(--muted);
  font-size: 0.9rem;
}
.ops-panel__status--error { color: var(--red); }

.cancel-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 10px;
}
.cancel-block {
  padding: 12px 14px;
  border: 1px solid var(--line);
  border-radius: 14px;
  background: var(--surface-2);
}
.cancel-block__title {
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--muted);
  font-weight: 700;
  margin-bottom: 6px;
}
.cancel-block ul {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.cancel-block li {
  display: grid;
  grid-template-columns: 1fr auto auto;
  gap: 8px;
  font-size: 0.82rem;
  align-items: baseline;
}
.cancel-row__key {
  color: var(--ink);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.cancel-row__count {
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}
.cancel-row__share {
  color: var(--muted);
  font-size: 0.78rem;
  font-variant-numeric: tabular-nums;
}

.cancel-detail {
  margin-top: 12px;
  border: 1px solid var(--line);
  border-radius: 12px;
  background: var(--surface-2);
}
.cancel-detail summary {
  padding: 10px 14px;
  cursor: pointer;
  font-weight: 600;
  color: var(--ink);
}
.cancel-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.82rem;
  background: var(--surface);
}
.cancel-table th,
.cancel-table td {
  padding: 6px 10px;
  border-top: 1px solid var(--line);
  text-align: left;
}
.cancel-table thead th {
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--muted);
}
.mono { font-variant-numeric: tabular-nums; font-weight: 700; }
</style>
