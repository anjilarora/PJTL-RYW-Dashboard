<script setup lang="ts">
/**
 * Landing page: nine launch-readiness gates in a single combined card-grid.
 * Each card shows the gate definition (formula + threshold) plus its slider
 * so users can see the threshold move the model output in one glance.
 */
const { role, apiPost } = useBackendApi()

interface KpiDoc {
  readiness_metrics?: Array<{
    metric_number: number
    key: string
    display_name?: string
    threshold?: number
    pass_rule?: string
    formula?: string
    target_phrase?: string
  }>
}

const ranges: Record<string, { min: number; max: number; step: number }> = {
  vehicle_utilization: { min: 0.5, max: 1.45, step: 0.01 },
  billed_utilization: { min: 0.5, max: 1.45, step: 0.01 },
  total_volume_pool: { min: 0.5, max: 2.0, step: 0.01 },
  revenue_per_kent_leg: { min: 25, max: 125, step: 0.5 },
  high_acuity_share: { min: 0, max: 0.35, step: 0.005 },
  non_billable_noshow: { min: 0, max: 0.35, step: 0.005 },
  road_hours_per_vehicle: { min: 4, max: 16, step: 0.1 },
  contract_concentration: { min: 0.05, max: 0.75, step: 0.01 },
  cost_per_road_hour: { min: 28, max: 85, step: 0.5 }
}

const defaults: Record<string, number> = {
  vehicle_utilization: 0.98,
  billed_utilization: 1.08,
  total_volume_pool: 1.25,
  revenue_per_kent_leg: 74,
  high_acuity_share: 0.07,
  non_billable_noshow: 0.08,
  road_hours_per_vehicle: 9.3,
  contract_concentration: 0.18,
  cost_per_road_hour: 48
}

const kpiError = ref("")
const kpis = ref<KpiDoc | null>(null)
const features = ref<Record<string, number>>({ ...defaults })
const predictError = ref("")
const predictBusy = ref(false)
const mlResult = ref<{
  prediction: string
  probability_ready: number
  classification_threshold: number
} | null>(null)

let debounceTimer: ReturnType<typeof setTimeout> | null = null

const orderedMetrics = computed(() => {
  const m = kpis.value?.readiness_metrics
  if (!m?.length) return []
  return [...m].sort((a, b) => a.metric_number - b.metric_number)
})

async function loadKpis() {
  kpiError.value = ""
  try {
    const res = await $fetch<{ data: KpiDoc }>("/api/backend/api/v1/kpis", {
      headers: { "X-Role": role.value }
    })
    kpis.value = res.data
  } catch {
    kpiError.value = "Could not load KPI definitions. Check that the backend is reachable."
  }
}

async function runPredict() {
  predictError.value = ""
  predictBusy.value = true
  try {
    const body: Record<string, number> = {}
    for (const k of Object.keys(defaults)) {
      body[k] = features.value[k] ?? defaults[k]
    }
    const res = await apiPost<{
      prediction: string
      probability_ready: number
      classification_threshold: number
    }>("/api/backend/api/v1/inference/predict", body)
    mlResult.value = {
      prediction: res.data.prediction,
      probability_ready: res.data.probability_ready,
      classification_threshold: res.data.classification_threshold
    }
  } catch {
    predictError.value = "Inference failed. Ensure the model is loaded and the backend is reachable."
    mlResult.value = null
  } finally {
    predictBusy.value = false
  }
}

function schedulePredict() {
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    void runPredict()
  }, 320)
}

function updateFeature(key: string, v: number) {
  features.value = { ...features.value, [key]: v }
  schedulePredict()
}

function resetAll() {
  features.value = { ...defaults }
  schedulePredict()
}

function formatMetricNumber(key: string, v: number) {
  if (key === "revenue_per_kent_leg" || key === "cost_per_road_hour") return v.toFixed(2)
  if (key === "road_hours_per_vehicle") return v.toFixed(2)
  return v.toFixed(4)
}

const PASS_RULE_SYMBOL: Record<string, string> = {
  gte: "≥",
  lte: "≤",
  lt: "<",
  gt: ">",
  eq: "=",
  ne: "≠"
}

function passRuleSymbol(rule: string): string {
  return PASS_RULE_SYMBOL[rule] ?? rule
}

function valuePassesGate(value: number, threshold: number, rule: string): boolean {
  switch (rule) {
    case "gte":
      return value >= threshold
    case "lte":
      return value <= threshold
    case "gt":
      return value > threshold
    case "lt":
      return value < threshold
    default:
      return false
  }
}

function gateStatusFor(metric: {
  key: string
  pass_rule?: string
  threshold?: number
}): { passing: boolean; label: string } | null {
  const { pass_rule: rule, threshold: t } = metric
  if (rule == null || t == null) return null
  const v = features.value[metric.key] ?? defaults[metric.key]
  if (typeof v !== "number") return null
  const passing = valuePassesGate(v, t, rule)
  return { passing, label: passing ? "pass" : "fail" }
}

const gateFailCount = computed(() => {
  const metrics = orderedMetrics.value
  if (!metrics.length) return 0
  return metrics.filter((m) => {
    const s = gateStatusFor(m)
    return s ? !s.passing : false
  }).length
})

const probeBusy = ref(false)
const probeResult = ref<
  | null
  | {
      key: string
      threshold: number
      eps: number
      baseline: number
      plus: number
      minus: number
      pPlus: number
      pMinus: number
      decisionPlus: string
      decisionMinus: string
    }
> (null)

function callPredict(body: Record<string, number>) {
  return apiPost<{
    prediction: string
    probability_ready: number
    classification_threshold: number
  }>("/api/backend/api/v1/inference/predict", body)
}

async function probeSensitivity(metric: {
  key: string
  pass_rule?: string
  threshold?: number
}) {
  const { pass_rule: rule, threshold: t, key } = metric
  if (rule == null || t == null) return
  const eps = Math.max(Math.abs(t) * 0.01, 1e-4)
  const baseline = features.value[key] ?? defaults[key]
  const plusSide = rule === "gte" || rule === "gt"
  const plusValue = plusSide ? t + eps : t - eps
  const minusValue = plusSide ? t - eps : t + eps
  const bodyTemplate = () => {
    const out: Record<string, number> = {}
    for (const k of Object.keys(defaults)) {
      out[k] = features.value[k] ?? defaults[k]
    }
    return out
  }
  probeBusy.value = true
  try {
    const bodyPlus = { ...bodyTemplate(), [key]: plusValue }
    const bodyMinus = { ...bodyTemplate(), [key]: minusValue }
    const [plusRes, minusRes] = await Promise.all([
      callPredict(bodyPlus),
      callPredict(bodyMinus)
    ])
    probeResult.value = {
      key,
      threshold: t,
      eps,
      baseline,
      plus: plusValue,
      minus: minusValue,
      pPlus: plusRes.data.probability_ready,
      pMinus: minusRes.data.probability_ready,
      decisionPlus: plusRes.data.prediction,
      decisionMinus: minusRes.data.prediction
    }
  } catch {
    probeResult.value = null
    predictError.value = "Sensitivity probe failed (backend unreachable?)."
  } finally {
    probeBusy.value = false
  }
}

onMounted(async () => {
  await loadKpis()
  await runPredict()
})
</script>

<template>
  <div id="main-content" class="landing-page" tabindex="-1">
    <PageHero
      eyebrow="Home · model sandbox"
      subtitle="PJTL × Ride YourWay"
      title="Launch-readiness what-if"
      description="These nine knobs drive the readiness model. Move any slider to see how combinations push the overall call toward Ready vs Not Ready. Each card also shows the gate rule that the underlying data has to clear."
    />

    <section v-if="kpiError" class="landing-panel landing-panel--error" role="alert">
      {{ kpiError }}
    </section>

    <section v-else-if="kpis && orderedMetrics.length" class="landing-panel">
      <div class="landing-head">
        <div>
          <div class="panel-eyebrow">
            Gate metrics &amp; what-if sliders
            <InfoTip
              label="What am I looking at?"
              content="Each card below is one of the nine launch gates. The formula and threshold match pjtl_kpis_and_formulas.json, the single source of truth shared with the readiness engine. Hover the info chip on a card to see its formula; drag the slider to see the ML decision change in real time."
            />
          </div>
          <h2>Nine gates, one sandbox</h2>
          <p class="muted">
            Every card combines the gate rule on top with its slider below. Pass / fail badges update
            instantly; p(Ready) at the top of the page comes from the live XGBoost model.
          </p>
        </div>
        <div class="landing-head__actions">
          <button type="button" class="secondary-button" @click="resetAll">Reset to defaults</button>
        </div>
      </div>

      <p v-if="predictError" class="error-text" role="alert">{{ predictError }}</p>

      <div v-if="mlResult" class="ml-banner" aria-live="polite">
        <div class="ml-banner__left">
          <span :class="['ml-banner__badge', mlResult.prediction.toLowerCase().includes('ready') && !mlResult.prediction.toLowerCase().includes('not') ? 'ml-banner__badge--pass' : 'ml-banner__badge--fail']">
            {{ mlResult.prediction }}
          </span>
          <span class="ml-banner__stat">
            <span class="ml-banner__stat-label">p(Ready)</span>
            <strong>{{ mlResult.probability_ready.toFixed(3) }}</strong>
          </span>
          <span class="ml-banner__stat">
            <span class="ml-banner__stat-label">Threshold</span>
            <strong>{{ mlResult.classification_threshold.toFixed(3) }}</strong>
          </span>
        </div>
        <div class="ml-banner__right">
          <span class="ml-banner__chip" :class="gateFailCount === 0 ? 'ml-banner__chip--ok' : 'ml-banner__chip--warn'">
            <span class="dot" aria-hidden="true" />
            {{ gateFailCount === 0 ? "All nine gates passing" : `${gateFailCount} of 9 gates failing` }}
          </span>
          <span v-if="predictBusy" class="ml-banner__updating">Updating…</span>
        </div>
      </div>

      <div v-if="probeResult" class="probe-panel" aria-live="polite">
        <div class="probe-panel__head">
          <p class="probe-panel__title">
            <strong>Probe · {{ probeResult.key }}</strong>
            <span class="probe-panel__sub">
              (&#177;1% of threshold {{ formatMetricNumber(probeResult.key, probeResult.threshold) }})
            </span>
          </p>
          <button
            type="button"
            class="probe-panel__dismiss"
            aria-label="Dismiss probe result"
            title="Dismiss"
            @click="probeResult = null"
          >
            ×
          </button>
        </div>
        <ul class="probe-rows">
          <li>
            Barely pass ({{ formatMetricNumber(probeResult.key, probeResult.plus) }}):
            <strong>{{ probeResult.decisionPlus }}</strong> · p={{ probeResult.pPlus.toFixed(3) }}
          </li>
          <li>
            Barely fail ({{ formatMetricNumber(probeResult.key, probeResult.minus) }}):
            <strong>{{ probeResult.decisionMinus }}</strong> · p={{ probeResult.pMinus.toFixed(3) }}
          </li>
        </ul>
      </div>

      <div class="gate-grid">
        <article
          v-for="m in orderedMetrics"
          :key="m.key"
          class="gate-grid__card"
          :class="[
            gateStatusFor(m)?.passing === true ? 'gate-grid__card--pass' : '',
            gateStatusFor(m)?.passing === false ? 'gate-grid__card--fail' : ''
          ]"
        >
          <header class="gate-grid__head">
            <div class="gate-grid__title">
              <span class="gate-grid__num">#{{ m.metric_number }}</span>
              <h3>{{ m.display_name || m.key }}</h3>
            </div>
            <span
              v-if="gateStatusFor(m)"
              class="gate-chip"
              :class="gateStatusFor(m)!.passing ? 'gate-chip--pass' : 'gate-chip--fail'"
            >
              {{ gateStatusFor(m)!.passing ? "pass" : "fail" }}
            </span>
          </header>
          <div v-if="m.target_phrase || m.formula" class="gate-grid__meta">
            <span v-if="m.pass_rule && m.threshold != null" class="gate-grid__rule">
              {{ passRuleSymbol(m.pass_rule) }} {{ formatMetricNumber(m.key, m.threshold) }}
            </span>
            <span v-if="m.target_phrase" class="gate-grid__target">{{ m.target_phrase }}</span>
            <InfoTip
              v-if="m.formula"
              label="Formula"
              :content="m.formula"
              placement="bottom"
            />
          </div>
          <div class="gate-grid__slider-row">
            <input
              :id="`f-${m.key}`"
              type="range"
              :min="ranges[m.key]?.min ?? 0"
              :max="ranges[m.key]?.max ?? 1"
              :step="ranges[m.key]?.step ?? 0.01"
              :value="features[m.key] ?? defaults[m.key]"
              class="slider"
              @input="updateFeature(m.key, Number(($event.target as HTMLInputElement).value))"
            />
            <span class="gate-grid__value">{{ formatMetricNumber(m.key, features[m.key] ?? defaults[m.key]) }}</span>
          </div>
          <div class="gate-grid__footer">
            <button
              type="button"
              class="probe-button"
              :disabled="probeBusy || m.pass_rule == null || m.threshold == null"
              :title="`Probe p(Ready) at +/- 1% of the ${m.display_name || m.key} threshold`"
              @click="probeSensitivity(m)"
            >
              Probe
            </button>
          </div>
        </article>
      </div>
    </section>
  </div>
</template>

<style scoped>
.landing-panel {
  padding: 22px 26px;
  border-radius: 20px;
  border: 1px solid var(--line);
  background: var(--surface);
  box-shadow: var(--shadow);
  margin-top: 14px;
}
.landing-panel--error { color: var(--red); }
.landing-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 14px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}
.landing-head h2 {
  margin: 4px 0 0;
  font-size: clamp(1.2rem, 2vw, 1.55rem);
  letter-spacing: -0.03em;
}
.muted { color: var(--muted); margin: 6px 0 0; max-width: 78ch; line-height: 1.55; }

.ml-banner {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  padding: 12px 14px;
  border-radius: 14px;
  border: 1px solid var(--line);
  background: linear-gradient(180deg, var(--surface-2) 0%, var(--surface) 100%);
  margin: 10px 0 14px;
}
.ml-banner__left,
.ml-banner__right {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
}
.ml-banner__badge {
  display: inline-flex;
  align-items: center;
  padding: 6px 14px;
  border-radius: 999px;
  font-weight: 800;
  font-size: 0.9rem;
  letter-spacing: 0.02em;
  text-transform: uppercase;
}
.ml-banner__badge--pass { background: var(--teal-soft); color: var(--teal); }
.ml-banner__badge--fail { background: var(--red-soft); color: var(--red); }
.ml-banner__stat { display: flex; flex-direction: column; font-variant-numeric: tabular-nums; }
.ml-banner__stat-label {
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--muted);
}
.ml-banner__stat strong {
  color: var(--ink);
  font-size: 1.1rem;
}
.ml-banner__chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 0.8rem;
  font-weight: 700;
}
.ml-banner__chip--ok { background: var(--teal-soft); color: var(--teal); }
.ml-banner__chip--warn { background: var(--red-soft); color: var(--red); }
.ml-banner__chip .dot { width: 8px; height: 8px; border-radius: 999px; background: currentColor; }
.ml-banner__updating { font-size: 0.82rem; color: var(--muted); }

.probe-panel {
  position: relative;
  margin: 0 0 1rem;
  padding: 0.6rem 0.85rem;
  border: 1px dashed var(--line);
  border-radius: 8px;
  background: color-mix(in srgb, var(--blue) 4%, transparent);
}
.probe-panel__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
}
.probe-panel__title { margin: 0; }
.probe-panel__sub { color: var(--muted); font-weight: 400; margin-left: 4px; }
.probe-panel__dismiss {
  appearance: none;
  border: 1px solid var(--line);
  background: var(--surface);
  color: var(--muted);
  width: 26px;
  height: 26px;
  border-radius: 999px;
  font-size: 1.05rem;
  line-height: 1;
  cursor: pointer;
  transition: background 140ms ease, color 140ms ease, border-color 140ms ease;
}
.probe-panel__dismiss:hover {
  background: var(--red-soft);
  color: var(--red);
  border-color: color-mix(in srgb, var(--red) 45%, transparent);
}
.probe-rows {
  list-style: none;
  padding: 0;
  margin: 0.25rem 0 0;
  font-size: 0.88rem;
  font-variant-numeric: tabular-nums;
}
.probe-rows li + li { margin-top: 0.15rem; }

.gate-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 12px;
}
.gate-grid__card {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 14px 16px;
  border-radius: 14px;
  border: 1px solid var(--line);
  background: var(--surface-2);
  border-top: 3px solid var(--muted);
}
.gate-grid__card--pass { border-top-color: var(--teal); }
.gate-grid__card--fail { border-top-color: var(--red); }
.gate-grid__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}
.gate-grid__title {
  display: inline-flex;
  align-items: baseline;
  gap: 8px;
  min-width: 0;
}
.gate-grid__title h3 {
  margin: 0;
  font-size: 0.98rem;
  color: var(--ink);
  letter-spacing: -0.01em;
  line-height: 1.2;
  flex: 1 1 auto;
}
.gate-grid__num {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 26px;
  padding: 1px 7px;
  border-radius: 999px;
  background: var(--blue-soft);
  color: var(--blue);
  font-size: 0.72rem;
  font-weight: 800;
}
.gate-chip {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 0.68rem;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  font-weight: 800;
  border: 1px solid var(--line);
}
.gate-chip--pass {
  color: var(--teal);
  border-color: color-mix(in srgb, var(--teal) 45%, transparent);
  background: var(--teal-soft);
}
.gate-chip--fail {
  color: var(--red);
  border-color: color-mix(in srgb, var(--red) 45%, transparent);
  background: var(--red-soft);
}
.gate-grid__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  font-size: 0.82rem;
  color: var(--muted);
  align-items: center;
}
.gate-grid__rule {
  font-variant-numeric: tabular-nums;
  font-weight: 700;
  color: var(--ink);
  background: var(--surface);
  border: 1px solid var(--line);
  padding: 2px 8px;
  border-radius: 999px;
}
.gate-grid__target {
  color: var(--blue);
  font-weight: 500;
}
.gate-grid__slider-row {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 10px;
  align-items: center;
  margin-top: 2px;
}
.gate-grid__value {
  font-size: 0.85rem;
  font-variant-numeric: tabular-nums;
  color: var(--ink);
  font-weight: 700;
  min-width: 5.5ch;
  text-align: right;
}
.slider {
  width: 100%;
  accent-color: var(--blue);
}
.gate-grid__footer {
  display: flex;
  justify-content: flex-end;
}
.probe-button {
  appearance: none;
  border: 1px solid var(--line-strong);
  background: var(--surface);
  color: var(--ink);
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 0.76rem;
  font-weight: 700;
  cursor: pointer;
}
.probe-button:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
.probe-button:hover:not(:disabled) {
  background: var(--blue-soft);
  border-color: var(--blue);
  color: var(--blue);
}
</style>
