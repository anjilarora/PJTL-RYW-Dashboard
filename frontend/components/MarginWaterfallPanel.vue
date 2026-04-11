<script setup lang="ts">
const props = defineProps<{
  revenue: number
  cost: number
  targetMarginPct?: number
}>()

const net = computed(() => props.revenue - props.cost)
const marginPct = computed(() => (props.revenue ? (net.value / props.revenue) * 100 : 0))
const target = computed(() => props.targetMarginPct ?? 25)

const marginDelta = computed(() => marginPct.value - target.value)
const marginTone = computed(() => {
  if (marginPct.value >= target.value) return "pass"
  if (marginPct.value >= 0) return "warn"
  return "fail"
})

const scale = computed(() => Math.max(props.revenue, props.cost, Math.abs(net.value)))
const pct = (v: number) => (scale.value ? (Math.abs(v) / scale.value) * 100 : 0)

const fmtMoney = (v: number) => `$${Math.round(v).toLocaleString("en-US")}`
const fmtPct = (v: number) => `${v >= 0 ? "+" : ""}${v.toFixed(1)}%`
</script>

<template>
  <article class="panel waterfall-panel">
    <div class="panel-eyebrow">
      Margin Waterfall
      <InfoTip
        label="About the margin waterfall"
        content="Weekly projected revenue minus weekly projected cost gives the net weekly margin. We compare the margin percentage against the launch target (default 25%). A negative net bar means the prospective market loses money at current pricing and cost assumptions."
      />
    </div>
    <h2>Revenue to Margin Bridge</h2>

    <div class="waterfall-summary">
      <div class="waterfall-summary__tile waterfall-summary__tile--revenue">
        <span class="tile-label">Weekly revenue</span>
        <span class="tile-value">{{ fmtMoney(revenue) }}</span>
      </div>
      <div class="waterfall-summary__tile waterfall-summary__tile--cost">
        <span class="tile-label">Weekly cost</span>
        <span class="tile-value">{{ fmtMoney(cost) }}</span>
      </div>
      <div class="waterfall-summary__tile" :class="`waterfall-summary__tile--${marginTone}`">
        <span class="tile-label">Net / margin</span>
        <span class="tile-value">{{ fmtMoney(net) }}</span>
        <span class="tile-sub">{{ marginPct.toFixed(1) }}% margin</span>
      </div>
    </div>

    <dl class="waterfall-bars">
      <div class="wf-row">
        <dt>Revenue</dt>
        <dd>
          <div class="wf-track">
            <div class="wf-fill wf-fill--revenue" :style="{ width: pct(revenue) + '%' }" />
          </div>
          <span class="wf-value">{{ fmtMoney(revenue) }}</span>
        </dd>
      </div>
      <div class="wf-row">
        <dt>Cost</dt>
        <dd>
          <div class="wf-track">
            <div class="wf-fill wf-fill--cost" :style="{ width: pct(cost) + '%' }" />
          </div>
          <span class="wf-value">{{ fmtMoney(cost) }}</span>
        </dd>
      </div>
      <div class="wf-row wf-row--net">
        <dt>Net</dt>
        <dd>
          <div class="wf-track wf-track--net">
            <span class="wf-zero-line" aria-hidden="true" />
            <div
              class="wf-fill"
              :class="net >= 0 ? 'wf-fill--net-positive' : 'wf-fill--net-negative'"
              :style="{ width: pct(net) + '%', [net >= 0 ? 'left' : 'right']: '50%' }"
            />
          </div>
          <span class="wf-value" :class="net >= 0 ? 'wf-value--pos' : 'wf-value--neg'">
            {{ net >= 0 ? '+' : '' }}{{ fmtMoney(net) }}
          </span>
        </dd>
      </div>
    </dl>

    <p class="waterfall-footnote" :class="`waterfall-footnote--${marginTone}`">
      <strong>{{ marginPct.toFixed(1) }}% margin</strong>
      is {{ fmtPct(marginDelta) }} vs the {{ target }}% launch target.
      <span v-if="marginTone === 'pass'">The market clears the margin gate.</span>
      <span v-else-if="marginTone === 'warn'">Margin is positive but below the launch target - pricing or cost structure needs work.</span>
      <span v-else>Margin is negative at current assumptions; the market loses money per week without intervention.</span>
    </p>
  </article>
</template>

<style scoped>
.waterfall-summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 12px;
  margin: 16px 0 20px;
}

.waterfall-summary__tile {
  padding: 14px 16px;
  border-radius: 12px;
  background: var(--surface-2);
  border: 1px solid var(--line);
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.tile-label {
  font-size: 0.78rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--muted);
}

.tile-value {
  font-size: 1.35rem;
  font-weight: 700;
  color: var(--ink);
  font-variant-numeric: tabular-nums;
}

.tile-sub {
  font-size: 0.82rem;
  color: var(--muted);
}

.waterfall-summary__tile--revenue {
  border-left: 4px solid var(--blue);
}
.waterfall-summary__tile--cost {
  border-left: 4px solid var(--amber);
}
.waterfall-summary__tile--pass {
  border-left: 4px solid var(--teal);
}
.waterfall-summary__tile--pass .tile-value { color: var(--teal); }
.waterfall-summary__tile--warn {
  border-left: 4px solid var(--amber);
}
.waterfall-summary__tile--warn .tile-value { color: var(--amber); }
.waterfall-summary__tile--fail {
  border-left: 4px solid var(--red);
}
.waterfall-summary__tile--fail .tile-value { color: var(--red); }

.waterfall-bars {
  margin: 0 0 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.wf-row {
  display: grid;
  grid-template-columns: 88px 1fr;
  align-items: center;
  gap: 12px;
  margin: 0;
}

.wf-row dt {
  font-size: 0.88rem;
  font-weight: 600;
  color: var(--muted);
}

.wf-row dd {
  margin: 0;
  display: flex;
  align-items: center;
  gap: 12px;
}

.wf-track {
  position: relative;
  height: 12px;
  flex: 1 1 auto;
  border-radius: 6px;
  background: var(--surface-3);
  overflow: hidden;
  border: 1px solid var(--line);
}

.wf-track--net {
  overflow: visible;
  background: transparent;
  border: none;
  height: 18px;
  display: flex;
  align-items: center;
}

.wf-track--net::before {
  content: "";
  position: absolute;
  inset: calc(50% - 6px) 0 auto 0;
  height: 12px;
  border-radius: 6px;
  background: var(--surface-3);
  border: 1px solid var(--line);
}

.wf-zero-line {
  position: absolute;
  top: 0;
  bottom: 0;
  left: 50%;
  width: 2px;
  background: var(--line-strong);
  z-index: 2;
}

.wf-fill {
  height: 100%;
  border-radius: 6px;
  min-width: 4px;
  transition: width 250ms ease;
}

.wf-fill--revenue {
  background: linear-gradient(90deg, var(--blue) 0%, var(--teal) 100%);
}
.wf-fill--cost {
  background: linear-gradient(90deg, var(--amber) 0%, #e65c44 100%);
}

.wf-fill--net-positive,
.wf-fill--net-negative {
  position: absolute;
  top: calc(50% - 6px);
  height: 12px;
  z-index: 1;
}
.wf-fill--net-positive {
  background: linear-gradient(90deg, var(--teal) 0%, var(--blue) 100%);
}
.wf-fill--net-negative {
  background: linear-gradient(90deg, var(--red) 0%, #e65c44 100%);
}

.wf-value {
  min-width: 100px;
  text-align: right;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  color: var(--ink);
}

.wf-value--pos {
  color: var(--teal);
}
.wf-value--neg {
  color: var(--red);
}

.waterfall-footnote {
  margin: 4px 0 0;
  padding: 10px 12px;
  border-radius: 10px;
  font-size: 0.9rem;
  line-height: 1.5;
  color: var(--ink);
  border: 1px solid var(--line);
  background: var(--surface-2);
}
.waterfall-footnote strong {
  font-variant-numeric: tabular-nums;
}
.waterfall-footnote--pass {
  border-left: 4px solid var(--teal);
}
.waterfall-footnote--warn {
  border-left: 4px solid var(--amber);
}
.waterfall-footnote--fail {
  border-left: 4px solid var(--red);
}

.panel-eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

@media (max-width: 560px) {
  .wf-row {
    grid-template-columns: 70px 1fr;
  }
  .wf-value {
    min-width: 80px;
  }
}
</style>
