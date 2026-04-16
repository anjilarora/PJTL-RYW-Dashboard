<script setup lang="ts">
import { buildEvaluatePayloadFromSession } from "~/composables/useViabilitySession"
import { gatesFromViability, marketFromViability, readinessFromViability } from "~/composables/viabilityDashboard"

const { data } = await useFetch("/api/dashboard")
const { role, lastError, apiPost } = useBackendApi()

const viability = ref<any>(null)
const message = ref("")
const uiError = ref("")
const dataSource = ref<"baseline" | "evaluation" | "upload">("baseline")
const lastUploadFile = ref<string>("")
const lastEvaluatedAt = ref<string>("")

const displayMarket = computed(() => {
  if (!data.value) return { name: "", summary: "", status: "", confidence: "" }
  const m = marketFromViability(viability.value, data.value.market)
  return {
    name: m.name,
    summary: m.summary,
    status: m.status ?? data.value.market.status,
    confidence: m.confidence ?? data.value.market.confidence,
    corridor: data.value.market.corridor,
    cityState: data.value.market.cityState
  }
})

const displayGates = computed(() => {
  if (!data.value) return []
  return gatesFromViability(viability.value, data.value.gates)
})

const displayReadiness = computed(() => {
  const d = data.value
  if (!d?.readiness) return undefined
  if (!viability.value?.report?.conditions?.length) return d.readiness
  return readinessFromViability(viability.value, d.readiness)
})

const liveEvaluationActive = computed(() => Boolean(viability.value?.report?.conditions?.length))

const dataSourceBanner = computed(() => {
  if (dataSource.value === "upload") {
    return {
      label: "Uploaded workbook",
      short: lastUploadFile.value ? `Uploaded · ${lastUploadFile.value}` : "Uploaded workbook",
      detail: lastUploadFile.value
        ? `Panels reflect the extracted base from ${lastUploadFile.value} combined with the bundled prospective intake example. Ran at ${lastEvaluatedAt.value}.`
        : "Panels reflect your latest upload.",
      tone: "upload" as const
    }
  }
  if (dataSource.value === "evaluation") {
    return {
      label: "Latest readiness evaluation",
      short: `Latest evaluation · ${lastEvaluatedAt.value}`,
      detail: `Panels reflect the most recent evaluation (ran at ${lastEvaluatedAt.value}). Historical / prospective data came from Market & readiness if saved, otherwise the default payload.`,
      tone: "evaluation" as const
    }
  }
  return {
    label: "Bundled January 2026 reference",
    short: "Baseline · Jan 2026 reference (Dec 29 2025 – Jan 31 2026)",
    detail: "Panels show the frozen five-week operating baseline (Dec 29 2025 – Jan 31 2026) that ships with the repo. Upload a workbook or click Run readiness evaluation to refresh.",
    tone: "baseline" as const
  }
})

type TabId = "gate" | "intake" | "margin" | "execution" | "audit" | "upload"
const activeDetailTab = ref<TabId>("gate")
const detailTabs: Array<{ id: TabId; label: string; hint?: string }> = [
  { id: "gate", label: "Gate detail" },
  { id: "intake", label: "Intake & programs" },
  { id: "margin", label: "Margin & sensitivity" },
  { id: "execution", label: "Execution queue" },
  { id: "audit", label: "Audit & lineage" },
  { id: "upload", label: "Upload & run" }
]

const selectedGateIndex = ref(0)
const selectedGate = computed(() => displayGates.value[selectedGateIndex.value])

function onGateSelected(idx: number) {
  selectedGateIndex.value = idx
  activeDetailTab.value = "gate"
}

const uploadBusy = ref(false)
const uploadError = ref("")
const uploadJobSteps = ref<Array<{ id: string; label: string; status: string; detail?: string; ts?: string }>>([])

async function runUploadPipeline(ev: Event) {
  const input = ev.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  uploadError.value = ""
  uploadJobSteps.value = []
  uploadBusy.value = true
  try {
    const fd = new FormData()
    fd.append("file", file)
    const start = await $fetch<{ data: { job_id: string } }>("/api/jobs/upload", {
      method: "POST",
      body: fd,
      headers: { "X-Role": role.value },
      timeout: 120_000
    })
    const jobId = start.data.job_id
    const deadline = Date.now() + 300_000
    let finished = false
    while (Date.now() < deadline && !finished) {
      const st = await $fetch<{
        data: { status: string; steps: typeof uploadJobSteps.value; error?: string; result?: { viability: unknown } }
      }>(`/api/backend/api/v1/jobs/${jobId}`, {
        headers: { "X-Role": role.value },
        timeout: 30_000
      })
      uploadJobSteps.value = [...st.data.steps]
      if (st.data.status === "completed" && st.data.result?.viability) {
        const v = st.data.result.viability as any
        viability.value = v
        dataSource.value = "upload"
        lastUploadFile.value = file.name
        lastEvaluatedAt.value = new Date().toLocaleTimeString()
        const ml = v.ml_readiness
        const mlBit =
          ml && typeof ml.prediction === "string"
            ? ` · ML: ${ml.prediction} (p_ready=${Number(ml.probability_ready).toFixed(3)})`
            : ""
        message.value = `Upload pipeline · ${v.readiness_state} · ${v.confidence_tier}${mlBit}`
        finished = true
      } else if (st.data.status === "failed") {
        uploadError.value = st.data.error || "Pipeline failed."
        finished = true
      } else {
        await new Promise((r) => setTimeout(r, 500))
      }
    }
    if (!finished && Date.now() >= deadline) {
      uploadError.value = "Pipeline timed out. Check server logs and workbook size."
    }
  } catch (e: unknown) {
    const err = e as { data?: { detail?: { message?: string } }; message?: string }
    uploadError.value = err?.data?.detail?.message ?? err?.message ?? "Upload failed."
  } finally {
    uploadBusy.value = false
    input.value = ""
  }
}

async function runViability() {
  uiError.value = ""
  try {
    const body = buildEvaluatePayloadFromSession()
    const res = await apiPost<any>("/api/backend/api/v1/viability/evaluate", body)
    viability.value = res.data
    dataSource.value = "evaluation"
    lastEvaluatedAt.value = new Date().toLocaleTimeString()
    const ml = res.data.ml_readiness
    const mlBit =
      ml && typeof ml.prediction === "string"
        ? ` · ML: ${ml.prediction} (p_ready=${Number(ml.probability_ready).toFixed(3)})`
        : ""
    message.value = `${res.data.readiness_state} · ${res.data.confidence_tier}${mlBit}`
  } catch {
    uiError.value = "Readiness evaluation failed. Retry or switch role if unauthorized."
  }
}
</script>

<template>
  <div v-if="data" id="main-content" tabindex="-1">
      <p v-if="liveEvaluationActive" class="live-banner" role="status">Live gate metrics from the latest viability run</p>

      <MarketHero
        :name="displayMarket.name"
        :city-state="displayMarket.cityState"
        :corridor="displayMarket.corridor"
        :status="displayMarket.status"
        :confidence="displayMarket.confidence"
        :summary="displayMarket.summary"
        :readiness="displayReadiness"
      />

      <div
        class="source-strip"
        :class="`source-strip--${dataSourceBanner.tone}`"
        role="status"
        aria-live="polite"
      >
        <span class="source-strip__dot" aria-hidden="true" />
        <span class="source-strip__label">{{ dataSourceBanner.label }}</span>
        <span class="source-strip__short" :title="dataSourceBanner.detail">{{ dataSourceBanner.short }}</span>
        <InfoTip label="Data source details" :content="dataSourceBanner.detail" placement="bottom" />
        <button
          type="button"
          class="source-strip__cta"
          @click="activeDetailTab = 'upload'"
          title="Jump to upload & run controls"
        >
          Refresh data
        </button>
      </div>

      <KpiSnapshotPanel
        :readiness="displayReadiness"
        :prospective="data.prospective"
        :source="dataSource"
      />

      <GateScorecard :rows="displayGates" @gate-selected="onGateSelected" />

      <section class="detail-tabs" aria-label="Additional decision detail">
        <div class="detail-tabs__nav" role="tablist">
          <button
            v-for="tab in detailTabs"
            :key="tab.id"
            type="button"
            role="tab"
            :id="`detail-tab-${tab.id}`"
            :aria-selected="activeDetailTab === tab.id"
            :aria-controls="`detail-panel-${tab.id}`"
            :tabindex="activeDetailTab === tab.id ? 0 : -1"
            class="detail-tabs__tab"
            :class="{ 'detail-tabs__tab--active': activeDetailTab === tab.id }"
            @click="activeDetailTab = tab.id"
          >
            {{ tab.label }}
          </button>
        </div>

        <div
          v-show="activeDetailTab === 'gate'"
          id="detail-panel-gate"
          role="tabpanel"
          aria-labelledby="detail-tab-gate"
        >
          <GateDetailPanel
            :row="selectedGate"
            :index="selectedGateIndex"
            :total-count="displayGates.length"
          />
        </div>

        <div
          v-show="activeDetailTab === 'intake'"
          id="detail-panel-intake"
          role="tabpanel"
          aria-labelledby="detail-tab-intake"
        >
          <IntakeSummaryPanel :programs="data.intakePrograms" />
        </div>

        <div
          v-show="activeDetailTab === 'margin'"
          id="detail-panel-margin"
          role="tabpanel"
          aria-labelledby="detail-tab-margin"
          class="panel-grid"
        >
          <MarginWaterfallPanel :revenue="data.prospective.weeklyRevenue" :cost="data.prospective.projectedCost" />
          <SensitivityScenarioPanel :assumptions="data.assumptions" />
        </div>

        <div
          v-show="activeDetailTab === 'execution'"
          id="detail-panel-execution"
          role="tabpanel"
          aria-labelledby="detail-tab-execution"
        >
          <RiskMitigationPanel :actions="data.riskActions" />
        </div>

        <div
          v-show="activeDetailTab === 'audit'"
          id="detail-panel-audit"
          role="tabpanel"
          aria-labelledby="detail-tab-audit"
        >
          <AuditTraceabilityPanel :governance="viability?.governance" :lineage-refs="viability?.lineage_refs" />
        </div>

        <div
          v-show="activeDetailTab === 'upload'"
          id="detail-panel-upload"
          role="tabpanel"
          aria-labelledby="detail-tab-upload"
          class="panel-grid"
        >
          <section class="panel action-panel">
            <div class="panel-eyebrow">
              Workbook upload
              <InfoTip
                label="What happens on upload"
                content="The server stages your .xlsx into code/inputs/, runs the Phase-1 extraction to write canonical CSVs into code/intermediates/phase1/, normalises inputs, evaluates all nine gates, and scores readiness with the exported XGBoost model in code/outputs/models/. Until you upload, panels show the bundled reference dataset."
              />
            </div>
            <h2>Upload daily-metrics workbook</h2>
            <p class="muted-note">
              <strong>Excel workbook (.xlsx) only</strong> — same shape as the bundled January 2026 example (Dec 29 2025 – Jan 31 2026).
              CSVs are not accepted here because the extractor reads named sheets directly from the workbook. Large files may take up to a minute.
            </p>
            <label class="upload-label">
              <span class="sr-only">Choose Excel workbook (.xlsx)</span>
              <input
                type="file"
                accept=".xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                :disabled="uploadBusy"
                class="file-input"
                @change="runUploadPipeline"
              />
            </label>
            <p v-if="uploadBusy" class="muted-note" aria-live="polite">Processing…</p>
            <p v-if="uploadError" class="error-text" role="alert">{{ uploadError }}</p>
            <ol v-if="uploadJobSteps.length" class="job-steps" aria-label="Pipeline progress">
              <li
                v-for="(s, idx) in uploadJobSteps"
                :key="`${s.id}-${idx}-${s.ts || ''}`"
                :class="['job-step', `job-step--${s.status}`]"
              >
                <span class="job-step__label">{{ s.label }}</span>
                <span v-if="s.detail" class="job-step__detail">{{ s.detail }}</span>
              </li>
            </ol>
          </section>

          <section class="panel action-panel">
            <div class="panel-eyebrow">
              Decision execution
              <InfoTip
                label="How readiness is computed"
                content="Readiness blends deterministic gate logic with a held-out XGBoost classifier trained on audited operating inputs. Both judgments are combined before returning a recommendation, so small changes near a gate boundary can flip the final call."
              />
            </div>
            <h2>Run readiness</h2>
            <p v-if="message" class="decision-message">{{ message }}</p>
            <p v-else class="muted-note">
              Submits this market's profile and historical payload to the readiness engine and refreshes every panel above with the returned decision. Use the data-source chip at the top of the page to confirm what you're looking at.
            </p>
            <p v-if="uiError" class="error-text" role="alert">{{ uiError }}</p>
            <p v-else-if="lastError" class="error-text" role="alert">{{ lastError.message }}</p>
            <button type="button" class="primary-button action-panel__cta" @click="runViability">
              <svg viewBox="0 0 24 24" width="14" height="14" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M8 5l11 7-11 7z" />
              </svg>
              Run readiness evaluation
            </button>
            <p class="muted-note">
              Uses the market profile and historical payload saved via <NuxtLink to="/market">Market &amp; readiness</NuxtLink>
              if present. Otherwise it submits the default market with an empty payload.
            </p>
            <div v-if="viability?.ml_readiness?.prediction" class="ml-readiness-panel">
              <div class="ml-readiness-panel__head">
                <strong>{{ viability.ml_readiness.prediction }}</strong>
                <span>p(Ready)={{ Number(viability.ml_readiness.probability_ready).toFixed(3) }}</span>
                <span class="ml-readiness-panel__version">model {{ viability.ml_readiness.model_version }}</span>
              </div>
              <ul v-if="viability.ml_readiness.top_drivers?.length" class="driver-list">
                <li v-for="(d, i) in viability.ml_readiness.top_drivers" :key="i">
                  {{ d.feature }}: impact={{ Number(d.impact).toFixed(4) }}
                </li>
              </ul>
            </div>
          </section>
        </div>
      </section>
  </div>
</template>

<style scoped>
.muted-note {
  margin-top: 0.6rem;
  font-size: 0.9rem;
  color: var(--muted);
  max-width: 42rem;
  line-height: 1.55;
}
.muted-note code {
  font-size: 0.85em;
}
.ml-readiness-panel {
  margin-top: 0.9rem;
  padding: 0.85rem 1rem;
  border-radius: 12px;
  background: var(--surface-2);
  border: 1px solid var(--line);
}
.ml-readiness-panel__head {
  display: flex;
  flex-wrap: wrap;
  gap: 10px 14px;
  align-items: baseline;
  color: var(--ink);
}
.ml-readiness-panel__head strong {
  color: var(--teal);
  letter-spacing: 0.04em;
  text-transform: uppercase;
  font-size: 0.92rem;
}
.ml-readiness-panel__version {
  color: var(--muted);
  font-size: 0.82rem;
}
.driver-list {
  margin: 0.6rem 0 0;
  padding-left: 1.25rem;
  font-size: 0.88rem;
  color: var(--muted);
}

.live-banner {
  margin: 14px 0 0;
  padding: 0.4rem 0.75rem;
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--teal);
  background: var(--teal-soft);
  border-radius: 999px;
  display: inline-block;
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
.upload-label {
  display: block;
  margin-top: 0.5rem;
}
.file-input {
  font-size: 0.9rem;
}
.job-steps {
  margin: 0.5rem 0 0;
  padding-left: 1.25rem;
  max-width: 48rem;
}
.job-step {
  margin-bottom: 0.35rem;
  font-size: 0.9rem;
}
.job-step--running {
  color: var(--blue);
  font-weight: 600;
}
.job-step--completed {
  color: var(--teal);
}
.job-step--failed {
  color: var(--red);
}
.job-step__detail {
  display: block;
  font-size: 0.85rem;
  color: var(--muted);
  margin-left: 0;
}

.source-strip {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  margin: 12px 0 0;
  padding: 6px 12px;
  border-radius: 999px;
  border: 1px solid var(--line);
  background: var(--surface-2);
  font-size: 0.82rem;
}
.source-strip__dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: var(--line-strong);
  flex-shrink: 0;
}
.source-strip--baseline .source-strip__dot { background: var(--maize); }
.source-strip--evaluation .source-strip__dot { background: var(--blue); }
.source-strip--upload .source-strip__dot { background: var(--teal); }

.source-strip__label {
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  font-size: 0.7rem;
  color: var(--muted);
}
.source-strip--baseline .source-strip__label { color: var(--maize-ink); }
.source-strip--evaluation .source-strip__label { color: var(--blue); }
.source-strip--upload .source-strip__label { color: var(--teal); }

.source-strip__short {
  color: var(--ink);
  font-weight: 600;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1 1 220px;
}
.source-strip__cta {
  margin-left: auto;
  appearance: none;
  border: 1px solid var(--line);
  background: transparent;
  color: var(--blue);
  font-size: 0.78rem;
  font-weight: 700;
  padding: 4px 10px;
  border-radius: 999px;
  cursor: pointer;
  transition: background 140ms ease, color 140ms ease;
}
.source-strip__cta:hover {
  background: var(--blue-soft);
}

.detail-tabs {
  margin-top: 14px;
}
.detail-tabs__nav {
  display: flex;
  gap: 4px;
  padding: 4px;
  margin-bottom: 12px;
  border-radius: 14px;
  background: var(--surface-2);
  border: 1px solid var(--line);
  overflow-x: auto;
  scrollbar-width: thin;
}
.detail-tabs__tab {
  appearance: none;
  border: 0;
  background: transparent;
  color: var(--muted);
  font-size: 0.88rem;
  font-weight: 600;
  padding: 8px 14px;
  border-radius: 10px;
  cursor: pointer;
  white-space: nowrap;
  transition: background 140ms ease, color 140ms ease;
}
.detail-tabs__tab:hover {
  color: var(--ink);
}
.detail-tabs__tab--active {
  background: var(--surface);
  color: var(--blue);
  box-shadow: 0 2px 8px color-mix(in srgb, var(--blue) 18%, transparent);
}
.detail-tabs__tab--active::after {
  content: "";
  display: block;
  margin: 4px auto 0;
  width: 14px;
  height: 3px;
  border-radius: 999px;
  background: linear-gradient(90deg, var(--blue), var(--maize));
}

.decision-message {
  color: var(--ink);
  line-height: 1.5;
  margin: 0 0 0.5rem;
  font-size: 0.92rem;
}

.panel-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
  margin-top: 14px;
}
@media (max-width: 1040px) {
  .panel-grid {
    grid-template-columns: 1fr;
  }
}

.action-panel {
  padding: 20px 22px;
}
.action-panel h2 {
  margin: 4px 0 0;
  font-size: clamp(1.1rem, 1.7vw, 1.4rem);
  letter-spacing: -0.03em;
}
.action-panel__cta {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin-top: 0.6rem;
  background: var(--blue);
  color: var(--white);
  border-color: transparent;
}
.action-panel__cta:hover {
  filter: brightness(1.08);
}
</style>
