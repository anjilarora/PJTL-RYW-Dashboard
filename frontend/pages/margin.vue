<script setup lang="ts">
/**
 * Margin calculator — a standalone page that lets anyone plug in weekly
 * revenue, cost, and a target margin and see the waterfall + sensitivity
 * scenarios light up. Defaults are seeded from the bundled dashboard data so
 * it lands on a sensible state even before a readiness evaluation runs.
 */
const { data } = await useFetch("/api/dashboard")

const revenue = ref<number>(0)
const cost = ref<number>(0)
const targetMarginPct = ref<number>(25)

watchEffect(() => {
  if (data.value?.prospective && revenue.value === 0 && cost.value === 0) {
    revenue.value = Number(data.value.prospective.weeklyRevenue ?? 0)
    cost.value = Number(data.value.prospective.projectedCost ?? 0)
    targetMarginPct.value = Number(data.value.readiness?.targetMarginPct ?? 25)
  }
})

const net = computed(() => revenue.value - cost.value)
const marginPct = computed(() => (revenue.value ? (net.value / revenue.value) * 100 : 0))
const marginDelta = computed(() => marginPct.value - targetMarginPct.value)

const tone = computed(() => {
  if (marginPct.value >= targetMarginPct.value) return "pass"
  if (marginPct.value >= 0) return "warn"
  return "fail"
})
const toneLabel = computed(() => {
  if (tone.value === "pass") return "On target"
  if (tone.value === "warn") return "Below target"
  return "Losing money"
})

function reset() {
  if (!data.value?.prospective) return
  revenue.value = Number(data.value.prospective.weeklyRevenue ?? 0)
  cost.value = Number(data.value.prospective.projectedCost ?? 0)
  targetMarginPct.value = Number(data.value.readiness?.targetMarginPct ?? 25)
}

const scenarios = computed(() => {
  const base = { revenue: revenue.value, cost: cost.value }
  return [
    { label: "+5% revenue", rev: base.revenue * 1.05, cost: base.cost },
    { label: "-5% cost", rev: base.revenue, cost: base.cost * 0.95 },
    { label: "+$70 per KL (parity)", rev: Math.max(base.revenue, 70 * 2500), cost: base.cost },
    { label: "-10% cost discipline", rev: base.revenue, cost: base.cost * 0.9 }
  ].map((s) => {
    const n = s.rev - s.cost
    const pct = s.rev ? (n / s.rev) * 100 : 0
    return { ...s, net: n, marginPct: pct }
  })
})

const fmtMoney = (v: number) => `$${Math.round(v).toLocaleString("en-US")}`
</script>

<template>
  <div id="main-content" class="margin-page" tabindex="-1">
    <PageHero
      eyebrow="Calculator"
      subtitle="Revenue · cost · margin"
      title="Margin calculator"
      description="Plug in weekly revenue, weekly cost, and a target margin. The waterfall shows where the money goes and the scenario row shows how quickly a few percentage points move the bottom line."
    />

    <section class="panel calc-panel">
      <div class="calc-head">
        <div>
          <div class="panel-eyebrow">
            Inputs
            <InfoTip
              label="Which numbers should I enter?"
              content="Use steady-state weekly figures. If you just ran a readiness evaluation, those numbers are pre-filled for you. Target margin defaults to the RYW launch gate of 25%."
            />
          </div>
          <h2 class="panel-title">Plug in your numbers</h2>
        </div>
        <button type="button" class="secondary-button" @click="reset">Reset to defaults</button>
      </div>

      <div class="calc-grid">
        <label class="calc-field">
          <span>Weekly revenue ($)</span>
          <input v-model.number="revenue" type="number" min="0" step="100" class="form-field" />
        </label>
        <label class="calc-field">
          <span>Weekly cost ($)</span>
          <input v-model.number="cost" type="number" min="0" step="100" class="form-field" />
        </label>
        <label class="calc-field">
          <span>Target margin (%)</span>
          <input v-model.number="targetMarginPct" type="number" min="0" max="100" step="0.5" class="form-field" />
        </label>
      </div>

      <div class="calc-result" :class="`calc-result--${tone}`">
        <div class="calc-result__tile">
          <span class="tile-label">Net / week</span>
          <span class="tile-value">{{ fmtMoney(net) }}</span>
        </div>
        <div class="calc-result__tile">
          <span class="tile-label">Margin</span>
          <span class="tile-value">{{ marginPct.toFixed(1) }}%</span>
        </div>
        <div class="calc-result__tile">
          <span class="tile-label">Vs target</span>
          <span class="tile-value">
            {{ marginDelta >= 0 ? "+" : "" }}{{ marginDelta.toFixed(1) }}pp
          </span>
        </div>
        <div class="calc-result__chip">
          <span class="dot" aria-hidden="true" />
          {{ toneLabel }}
        </div>
      </div>
    </section>

    <section class="panel-grid">
      <MarginWaterfallPanel :revenue="revenue" :cost="cost" :target-margin-pct="targetMarginPct" />

      <article class="panel">
        <div class="panel-eyebrow">
          Scenarios
          <InfoTip
            label="About quick scenarios"
            content="Each chip perturbs one lever (revenue or cost) and reports the new weekly margin. Use them as a fast sense-check before running the full sensitivity panel on the dashboard."
          />
        </div>
        <h2 class="panel-title">What-if the lever moves</h2>
        <ul class="scenario-list">
          <li
            v-for="s in scenarios"
            :key="s.label"
            :class="['scenario-row', s.marginPct >= targetMarginPct ? 'scenario-row--pass' : s.marginPct >= 0 ? 'scenario-row--warn' : 'scenario-row--fail']"
          >
            <div class="scenario-row__head">
              <strong>{{ s.label }}</strong>
              <span class="scenario-row__margin">{{ s.marginPct.toFixed(1) }}%</span>
            </div>
            <div class="scenario-row__numbers">
              <span>rev {{ fmtMoney(s.rev) }}</span>
              <span>cost {{ fmtMoney(s.cost) }}</span>
              <span class="scenario-row__net">net {{ fmtMoney(s.net) }}</span>
            </div>
          </li>
        </ul>
      </article>
    </section>
  </div>
</template>

<style scoped>
.margin-page {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.calc-panel {
  padding: 22px;
}
.calc-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 16px;
}
.panel-title {
  margin: 2px 0 0;
  font-size: clamp(1.1rem, 1.7vw, 1.4rem);
  letter-spacing: -0.03em;
}
.calc-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}
.calc-field span {
  display: block;
  font-size: 0.82rem;
  color: var(--muted);
  margin-bottom: 4px;
}
.calc-result {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
  padding: 12px 14px;
  border-radius: 14px;
  border: 1px solid var(--line);
  background: var(--surface-2);
}
.calc-result--pass { border-left: 4px solid var(--teal); }
.calc-result--warn { border-left: 4px solid var(--amber); }
.calc-result--fail { border-left: 4px solid var(--red); }
.calc-result__tile {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}
.tile-label {
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--muted);
}
.tile-value {
  font-size: 1.25rem;
  font-weight: 800;
  font-variant-numeric: tabular-nums;
  color: var(--ink);
}
.calc-result__chip {
  margin-left: auto;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 12px;
  border-radius: 999px;
  font-size: 0.8rem;
  font-weight: 800;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}
.calc-result--pass .calc-result__chip { background: var(--teal-soft); color: var(--teal); }
.calc-result--warn .calc-result__chip { background: var(--amber-soft); color: var(--amber); }
.calc-result--fail .calc-result__chip { background: var(--red-soft); color: var(--red); }
.calc-result__chip .dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: currentColor;
}

.panel-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}
@media (max-width: 1040px) {
  .panel-grid {
    grid-template-columns: 1fr;
  }
}

.scenario-list {
  list-style: none;
  margin: 14px 0 0;
  padding: 0;
  display: grid;
  gap: 8px;
}
.scenario-row {
  padding: 10px 12px;
  border-radius: 12px;
  background: var(--surface-2);
  border: 1px solid var(--line);
  border-left: 4px solid var(--muted);
}
.scenario-row--pass { border-left-color: var(--teal); }
.scenario-row--warn { border-left-color: var(--amber); }
.scenario-row--fail { border-left-color: var(--red); }
.scenario-row__head {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  font-size: 0.92rem;
}
.scenario-row__margin {
  font-weight: 800;
  font-variant-numeric: tabular-nums;
}
.scenario-row--pass .scenario-row__margin { color: var(--teal); }
.scenario-row--warn .scenario-row__margin { color: var(--amber); }
.scenario-row--fail .scenario-row__margin { color: var(--red); }
.scenario-row__numbers {
  margin-top: 4px;
  display: flex;
  gap: 14px;
  flex-wrap: wrap;
  font-size: 0.82rem;
  color: var(--muted);
  font-variant-numeric: tabular-nums;
}
.scenario-row__net { color: var(--ink); font-weight: 700; }
</style>
