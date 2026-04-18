<script setup lang="ts">
/**
 * D8 — Revenue per Kent-Leg by payer.
 *
 * The fleet target is $70/KL (Gate 4). This panel renders every payer on a
 * horizontal bar chart centred on $70: bars extending right indicate payers
 * lifting the average, bars extending left indicate payers dragging it down.
 * The fleet-wide blended rate is shown at the top for reference.
 */
type Payer = {
  payer_id: string
  revenue: number | null
  kent_legs: number | null
  trips: number | null
  revenue_per_kentleg: number | null
  lift_vs_70: number | null
}

const props = defineProps<{
  payers: Payer[]
  target: number
  fleetRevPerKentleg: number | null
  loading?: boolean
  error?: string | null
}>()

const minKl = ref(10)

const filtered = computed(() =>
  props.payers
    .filter((p) => (p.kent_legs ?? 0) >= minKl.value)
    .sort((a, b) => (b.kent_legs ?? 0) - (a.kent_legs ?? 0))
)

const maxAbsLift = computed(() => {
  let max = 5
  for (const p of filtered.value) {
    const v = Math.abs(p.lift_vs_70 ?? 0)
    if (v > max) max = v
  }
  return max
})

const liftPositiveCount = computed(() => filtered.value.filter((p) => (p.lift_vs_70 ?? 0) >= 0).length)
const liftNegativeCount = computed(() => filtered.value.filter((p) => (p.lift_vs_70 ?? 0) < 0).length)

function currency(v: number | null | undefined): string {
  if (v === null || v === undefined) return "—"
  return `$${v.toFixed(1)}`
}
function short(v: number | null): string {
  if (v === null || v === undefined) return "—"
  return v.toLocaleString("en-US", { maximumFractionDigits: 0 })
}

function barStyle(p: Payer) {
  const lift = p.lift_vs_70 ?? 0
  const pct = Math.min(100, Math.abs(lift) / maxAbsLift.value * 50)
  if (lift >= 0) {
    return {
      left: "50%",
      width: `${pct}%`,
      background: lift >= 0 ? "var(--teal)" : "var(--red)"
    }
  }
  return {
    right: "50%",
    width: `${pct}%`,
    background: "var(--red)"
  }
}
</script>

<template>
  <section class="panel ops-panel">
    <header class="ops-panel__head">
      <div class="panel-eyebrow">
        D8: Revenue per Kent-Leg
        <InfoTip
          label="Rev / Kent-Leg lift"
          content="Bars extend right of the $70 line when a payer lifts the fleet average above the Gate-4 target; left when it drags it below. Filter by minimum Kent-Leg volume to focus on material payers. The fleet-wide blended rate includes every payer regardless of volume."
        />
      </div>
      <h2>Revenue per Kent-Leg by payer</h2>
      <p class="ops-panel__caption">
        Gate 4 target: <strong>${{ target.toFixed(0) }}</strong> · Fleet blended rate:
        <strong :class="`value-${(fleetRevPerKentleg ?? 0) >= target ? 'pass' : 'fail'}`">{{ currency(fleetRevPerKentleg) }}</strong>
        · {{ liftPositiveCount }} payers lifting / {{ liftNegativeCount }} dragging.
      </p>
    </header>

    <div v-if="loading" class="ops-panel__status">Loading…</div>
    <div v-else-if="error" class="ops-panel__status ops-panel__status--error">{{ error }}</div>
    <div v-else-if="!payers.length" class="ops-panel__status">No payer rev/KL data.</div>

    <template v-else>
      <label class="min-kl">
        Minimum Kent-Legs
        <input v-model.number="minKl" type="number" min="0" step="5" />
        <span class="min-kl__hint">(hides payers below the volume threshold; {{ filtered.length }} of {{ payers.length }} shown)</span>
      </label>

      <ul class="waterfall">
        <li v-for="p in filtered" :key="p.payer_id" class="waterfall__row">
          <div class="waterfall__name">{{ p.payer_id }}</div>
          <div class="waterfall__chart">
            <div class="waterfall__axis" aria-hidden="true" />
            <div class="waterfall__bar" :style="barStyle(p)" />
          </div>
          <div class="waterfall__value">
            <strong :class="`value-${(p.revenue_per_kentleg ?? 0) >= target ? 'pass' : 'fail'}`">{{ currency(p.revenue_per_kentleg) }}</strong>
            <span class="waterfall__lift">{{ (p.lift_vs_70 ?? 0) >= 0 ? "+" : "" }}{{ currency(p.lift_vs_70) }}</span>
          </div>
          <div class="waterfall__meta">
            {{ short(p.kent_legs) }} KL · {{ short(p.trips) }} trips
          </div>
        </li>
      </ul>
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
.ops-panel__caption strong { font-variant-numeric: tabular-nums; color: var(--ink); }
.value-pass { color: var(--teal); }
.value-fail { color: var(--red); }
.ops-panel__status {
  padding: 10px 12px;
  color: var(--muted);
  font-size: 0.9rem;
}
.ops-panel__status--error { color: var(--red); }

.min-kl {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 0.82rem;
  color: var(--muted);
  font-weight: 600;
  margin-bottom: 8px;
}
.min-kl input {
  width: 72px;
  padding: 4px 8px;
  border-radius: 8px;
  border: 1px solid var(--line);
  background: var(--surface-2);
  color: var(--ink);
  font: inherit;
  font-variant-numeric: tabular-nums;
}
.min-kl__hint {
  color: var(--muted);
  font-weight: 500;
}

.waterfall {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.waterfall__row {
  display: grid;
  grid-template-columns: minmax(140px, 220px) 1fr minmax(110px, auto) minmax(110px, auto);
  gap: 10px;
  align-items: center;
  padding: 6px 10px;
  border-radius: 10px;
  background: var(--surface-2);
  border: 1px solid var(--line);
}
.waterfall__name {
  font-size: 0.84rem;
  font-weight: 600;
  color: var(--ink);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.waterfall__chart {
  position: relative;
  height: 12px;
  background: color-mix(in srgb, var(--line) 60%, transparent);
  border-radius: 999px;
  overflow: hidden;
}
.waterfall__axis {
  position: absolute;
  top: -2px;
  bottom: -2px;
  left: 50%;
  width: 2px;
  background: var(--ink);
  opacity: 0.35;
}
.waterfall__bar {
  position: absolute;
  top: 0;
  bottom: 0;
  border-radius: 999px;
}
.waterfall__value {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
  align-items: baseline;
  font-size: 0.84rem;
}
.waterfall__value strong { font-variant-numeric: tabular-nums; }
.waterfall__lift {
  color: var(--muted);
  font-size: 0.78rem;
  font-variant-numeric: tabular-nums;
}
.waterfall__meta {
  font-size: 0.76rem;
  color: var(--muted);
  font-variant-numeric: tabular-nums;
  text-align: right;
}

@media (max-width: 820px) {
  .waterfall__row {
    grid-template-columns: 1fr;
    gap: 4px;
  }
  .waterfall__value,
  .waterfall__meta { justify-content: flex-start; text-align: left; }
}
</style>
