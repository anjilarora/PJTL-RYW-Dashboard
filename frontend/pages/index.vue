<script setup lang="ts">
/**
 * Landing: PJTL/RYW gate definitions + interactive nine-feature what-if (XGBoost).
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
    kpiError.value = "Could not load KPI definitions. Check backend and role."
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
    predictError.value = "Inference failed. Ensure the model is loaded and you are authorized as analyst."
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

/** Same decimal rules for slider readout and gate threshold hints. */
function formatMetricNumber(key: string, v: number) {
  if (key === "revenue_per_kent_leg" || key === "cost_per_road_hour") return v.toFixed(2)
  if (key === "road_hours_per_vehicle") return v.toFixed(2)
  return v.toFixed(4)
}

function formatSliderValue(key: string, v: number) {
  return formatMetricNumber(key, v)
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

/** Deterministic 9-gate AND rule mirrored client-side so users see which
 *  gate(s) they are near independent of the ML banner above. */
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

/** One-click probe: nudge the focused slider by +/- 1% of its threshold and
 *  read back p(Ready) at each side so the user can verify the flip. */
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

function gateThresholdTitle(metric: {
  pass_rule?: string
  threshold?: number
  display_name?: string
  key: string
}): string {
  const { pass_rule: rule, threshold: t } = metric
  if (rule == null || t == null) return ""
  const label = metric.display_name || metric.key
  const n = formatMetricNumber(metric.key, t)
  switch (rule) {
    case "gte":
      return `Pass when ${label} is greater than or equal to ${n} (${n} or higher).`
    case "lte":
      return `Pass when ${label} is less than or equal to ${n} (${n} or lower).`
    case "lt":
      return `Pass when ${label} is strictly less than ${n}.`
    case "gt":
      return `Pass when ${label} is strictly greater than ${n}.`
    case "eq":
      return `Pass when ${label} equals ${n}.`
    case "ne":
      return `Pass when ${label} is not equal to ${n}.`
    default:
      return `Pass rule ${rule} at ${n}.`
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
      eyebrow="Model sandbox"
      subtitle="Home · PJTL × Ride YourWay"
      title="Launch readiness what-if"
      description="PJTL gate rules define Go / No-Go thresholds. The exported XGBoost model estimates readiness from the same nine operational features. Adjust sliders below to see how combinations move the model toward Ready vs Not Ready."
    />


    <section v-if="kpiError" class="landing-panel landing-panel--error" role="alert">
      {{ kpiError }}
    </section>

    <section v-else-if="kpis" class="landing-panel">
      <h2>PJTL / RYW gate metrics and formulae</h2>
      <p class="muted">
        Thresholds and pass rules below match <code>pjtl_kpis_and_formulas.json</code> (shared with the viability engine and ML
        label derivation).
      </p>
      <ul class="formula-list">
        <li v-for="m in orderedMetrics" :key="m.key" class="formula-item">
          <strong>{{ m.display_name || m.key }}</strong>
          <span class="tag">#{{ m.metric_number }}</span>
          <span v-if="m.target_phrase" class="target">{{ m.target_phrase }}</span>
          <p v-if="m.formula" class="formula-text">{{ m.formula }}</p>
        </li>
      </ul>
    </section>

    <section v-if="orderedMetrics.length" class="landing-panel">
      <h2>What-if: nine XGBoost inputs</h2>
        <p class="muted">
        p(Ready) uses the backend model’s probability for the positive class; the decision uses the tuned classification
        threshold (shown below when inference succeeds).
      </p>
      <p v-if="predictError" class="error-text" role="alert">{{ predictError }}</p>
      <div v-if="mlResult" class="ml-banner" aria-live="polite">
        <p>
          <strong>{{ mlResult.prediction }}</strong>
          · p(Ready)={{ mlResult.probability_ready.toFixed(3) }} · threshold={{ mlResult.classification_threshold.toFixed(3) }}
        </p>
        <p class="muted gate-summary">
          <span v-if="gateFailCount === 0">All nine gates passing.</span>
          <span v-else>{{ gateFailCount }} of 9 gates failing.</span>
        </p>
      </div>
      <p v-if="predictBusy" class="muted">Updating…</p>

      <div v-if="probeResult" class="probe-panel" aria-live="polite">
        <p>
          <strong>Sensitivity probe: {{ probeResult.key }}</strong>
          (&#177;1% of threshold {{ formatMetricNumber(probeResult.key, probeResult.threshold) }})
        </p>
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

      <div class="sliders-grid">
        <div v-for="m in orderedMetrics" :key="m.key" class="slider-row">
          <label :for="`f-${m.key}`" class="slider-label">
            {{ m.display_name || m.key }}
            <span v-if="m.pass_rule && m.threshold != null" class="threshold-hint" :title="gateThresholdTitle(m)">
              <span class="sr-only">{{ gateThresholdTitle(m) }}</span>
              <span aria-hidden="true" class="threshold-hint__visible">
                ({{ passRuleSymbol(m.pass_rule) }} {{ formatMetricNumber(m.key, m.threshold) }})
              </span>
            </span>
            <span
              v-if="gateStatusFor(m)"
              class="gate-chip"
              :class="gateStatusFor(m)!.passing ? 'gate-chip--pass' : 'gate-chip--fail'"
              :aria-label="gateStatusFor(m)!.passing ? 'Gate passing' : 'Gate failing'"
            >
              {{ gateStatusFor(m)!.passing ? "pass" : "fail" }}
            </span>
          </label>
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
          <span class="slider-value">{{ formatSliderValue(m.key, features[m.key] ?? defaults[m.key]) }}</span>
          <button
            type="button"
            class="probe-button"
            :disabled="probeBusy || m.pass_rule == null || m.threshold == null"
            :title="`Probe flip at +/- 1% of ${m.display_name || m.key} threshold`"
            @click="probeSensitivity(m)"
          >
            Probe
          </button>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
/* Layout + typography: see assets/css/main.css (.landing-*) */
.landing-logo {
  margin-bottom: 0.4rem;
}
.landing-header__intro h1 {
  margin-top: 0;
}
.role-inline {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.9rem;
}
.formula-list {
  list-style: none;
  padding: 0;
  margin: 0;
}
.formula-item {
  padding: 0.65rem 0;
  border-bottom: 1px solid var(--line);
}
.formula-item:last-child {
  border-bottom: none;
}
.tag {
  display: inline-block;
  margin-left: 0.35rem;
  font-size: 0.75rem;
  color: var(--muted-2);
}
.target {
  display: block;
  font-size: 0.85rem;
  color: var(--blue);
  margin-top: 0.2rem;
}
.formula-text {
  margin: 0.35rem 0 0;
  font-size: 0.88rem;
  color: var(--muted);
}
.sliders-grid {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
.slider-row {
  display: grid;
  grid-template-columns: 1fr minmax(0, 12rem) 4.5rem auto;
  gap: 0.5rem 0.75rem;
  align-items: center;
}
@media (max-width: 640px) {
  .slider-row {
    grid-template-columns: 1fr;
  }
}
.gate-chip {
  display: inline-block;
  margin-left: 0.5rem;
  padding: 0.05rem 0.45rem;
  border-radius: 9999px;
  font-size: 0.68rem;
  letter-spacing: 0.02em;
  text-transform: uppercase;
  font-weight: 600;
  border: 1px solid var(--line);
  vertical-align: middle;
}
.gate-chip--pass {
  color: var(--green, #0a7f46);
  border-color: var(--green, #0a7f46);
  background-color: color-mix(in srgb, var(--green, #0a7f46) 12%, transparent);
}
.gate-chip--fail {
  color: var(--red, #b3261e);
  border-color: var(--red, #b3261e);
  background-color: color-mix(in srgb, var(--red, #b3261e) 12%, transparent);
}
.gate-summary {
  margin: 0.25rem 0 0;
  font-size: 0.82rem;
}
.probe-button {
  appearance: none;
  border: 1px solid var(--line);
  background: transparent;
  color: var(--ink);
  padding: 0.2rem 0.55rem;
  border-radius: 6px;
  font-size: 0.78rem;
  cursor: pointer;
}
.probe-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.probe-button:hover:not(:disabled) {
  background: color-mix(in srgb, var(--blue) 10%, transparent);
}
.probe-panel {
  margin: 0.5rem 0 1rem;
  padding: 0.6rem 0.85rem;
  border: 1px dashed var(--line);
  border-radius: 8px;
  background: color-mix(in srgb, var(--blue) 4%, transparent);
}
.probe-rows {
  list-style: none;
  padding: 0;
  margin: 0.25rem 0 0;
  font-size: 0.88rem;
  font-variant-numeric: tabular-nums;
}
.probe-rows li + li {
  margin-top: 0.15rem;
}
.slider-label {
  font-size: 0.88rem;
  color: var(--ink);
}
.threshold-hint {
  display: block;
  font-size: 0.78rem;
  color: var(--muted-2);
  font-weight: 500;
  margin-top: 0.15rem;
}
.threshold-hint__visible {
  font-variant-numeric: tabular-nums;
}
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}
.slider {
  width: 100%;
  accent-color: var(--blue);
}
.slider-value {
  font-size: 0.85rem;
  font-variant-numeric: tabular-nums;
  text-align: right;
  color: var(--muted);
}
</style>
