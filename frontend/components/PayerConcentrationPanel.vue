<script setup lang="ts">
/**
 * D5 — Payer concentration.
 *
 * Gate 8 says no single payer should exceed 20% of either revenue or volume
 * (Kent-Legs). This panel lists every payer sorted by revenue share, flags
 * caps, and renders a stacked-bar style view so a user can see the
 * concentration fingerprint at a glance. ``warnings`` come pre-computed from
 * the service layer so we can render a call-out even before the table
 * renders.
 */
type Payer = {
  payer_id: string
  kent_legs: number | null
  revenue: number | null
  trips: number | null
  vol_share: number | null
  rev_share: number | null
  over_20pct_vol: boolean | null
  over_20pct_rev: boolean | null
  near_cap: boolean | null
}

const props = defineProps<{
  payers: Payer[]
  warnings: Payer[]
  capVolume: number
  capRevenue: number
  loading?: boolean
  error?: string | null
}>()

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

function rowTone(p: Payer): string {
  if (p.over_20pct_rev || p.over_20pct_vol) return "fail"
  if (p.near_cap) return "warn"
  return "neutral"
}
</script>

<template>
  <section class="panel ops-panel">
    <header class="ops-panel__head">
      <div class="panel-eyebrow">
        D5: Payer concentration
        <InfoTip
          label="Gate 8: payer concentration"
          content="Gate 8 rejects launch when any single payer exceeds 20% of revenue or 20% of Kent-Leg volume. Near-cap means 90% of the cap. ``vol_share`` uses Kent-Legs; ``rev_share`` uses revenue. Both shares are computed against the fleet total from contract_volume_base.csv."
        />
      </div>
      <h2>Largest payers &amp; 20% cap compliance</h2>
    </header>

    <div v-if="loading" class="ops-panel__status">Loading payer concentration…</div>
    <div v-else-if="error" class="ops-panel__status ops-panel__status--error">{{ error }}</div>
    <div v-else-if="!payers.length" class="ops-panel__status">No payer data.</div>

    <template v-else>
      <div
        v-if="warnings.length"
        class="payer-warn"
        role="status"
      >
        <strong>{{ warnings.length }} payer{{ warnings.length === 1 ? "" : "s" }} breach or nearly breach the 20% cap:</strong>
        <span>{{ warnings.map((w) => w.payer_id).join(" · ") }}</span>
      </div>
      <p v-else class="payer-ok" role="status">No payer exceeds the 20% volume or revenue cap.</p>

      <div class="payer-table-wrap">
        <table class="payer-table" aria-label="Payer concentration">
          <thead>
            <tr>
              <th scope="col">Payer</th>
              <th scope="col">Volume share</th>
              <th scope="col">Revenue share</th>
              <th scope="col">Kent-Legs</th>
              <th scope="col">Revenue</th>
              <th scope="col">Status</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="p in payers" :key="p.payer_id" :class="`payer-row payer-row--${rowTone(p)}`">
              <th scope="row">{{ p.payer_id }}</th>
              <td>
                <div class="share-cell">
                  <div class="share-bar">
                    <div class="share-bar__fill" :style="{ width: `${Math.min(100, (p.vol_share ?? 0) * 100 * 4)}%`, background: (p.over_20pct_vol ? 'var(--red)' : (p.vol_share ?? 0) > capVolume * 0.9 ? 'var(--amber)' : 'var(--blue)') }" />
                    <div class="share-bar__cap" :style="{ left: `${capVolume * 100 * 4}%` }" />
                  </div>
                  <span>{{ pct(p.vol_share) }}</span>
                </div>
              </td>
              <td>
                <div class="share-cell">
                  <div class="share-bar">
                    <div class="share-bar__fill" :style="{ width: `${Math.min(100, (p.rev_share ?? 0) * 100 * 4)}%`, background: (p.over_20pct_rev ? 'var(--red)' : (p.rev_share ?? 0) > capRevenue * 0.9 ? 'var(--amber)' : 'var(--teal)') }" />
                    <div class="share-bar__cap" :style="{ left: `${capRevenue * 100 * 4}%` }" />
                  </div>
                  <span>{{ pct(p.rev_share) }}</span>
                </div>
              </td>
              <td class="mono">{{ short(p.kent_legs) }}</td>
              <td class="mono">{{ currency(p.revenue) }}</td>
              <td>
                <StatusPill v-if="p.over_20pct_rev || p.over_20pct_vol" label="Over cap" tone="fail" size="sm" />
                <StatusPill v-else-if="p.near_cap" label="Near cap" tone="provisional" size="sm" />
                <StatusPill v-else label="Within cap" tone="pass" size="sm" />
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <p class="payer-footnote">
        Bars are scaled so the dashed line at {{ (capVolume * 100).toFixed(0) }}% (≈ one-quarter of the bar) represents the gate 8 cap.
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
.ops-panel__status {
  padding: 10px 12px;
  color: var(--muted);
  font-size: 0.9rem;
}
.ops-panel__status--error { color: var(--red); }

.payer-warn {
  margin-bottom: 10px;
  padding: 8px 12px;
  border: 1px solid color-mix(in srgb, var(--red) 45%, transparent);
  border-radius: 12px;
  background: var(--red-soft);
  color: var(--red);
  font-size: 0.88rem;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}
.payer-ok {
  margin: 0 0 10px;
  padding: 8px 12px;
  border-radius: 12px;
  background: var(--teal-soft);
  color: var(--teal);
  font-size: 0.88rem;
  border: 1px solid color-mix(in srgb, var(--teal) 40%, transparent);
}

.payer-table-wrap { overflow-x: auto; }
.payer-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.88rem;
}
.payer-table th,
.payer-table td {
  padding: 8px 10px;
  text-align: left;
  border-bottom: 1px solid var(--line);
}
.payer-table thead th {
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--muted);
}
.payer-table tbody th {
  font-weight: 700;
  color: var(--ink);
}
.payer-row--fail th { color: var(--red); }

.share-cell {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 160px;
}
.share-bar {
  position: relative;
  flex: 1 1 auto;
  height: 8px;
  background: var(--surface-2);
  border: 1px solid var(--line);
  border-radius: 999px;
  overflow: hidden;
  min-width: 80px;
}
.share-bar__fill {
  height: 100%;
  border-radius: 999px;
  transition: width 240ms ease;
}
.share-bar__cap {
  position: absolute;
  top: -3px;
  width: 2px;
  height: 14px;
  background: var(--ink);
  opacity: 0.45;
}
.share-cell span {
  font-variant-numeric: tabular-nums;
  font-weight: 700;
  min-width: 52px;
  text-align: right;
}
.mono { font-variant-numeric: tabular-nums; }

.payer-footnote {
  margin: 8px 0 0;
  font-size: 0.78rem;
  color: var(--muted);
}
</style>
