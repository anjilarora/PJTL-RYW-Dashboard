<script setup lang="ts">
/**
 * Market & readiness – prospective-intake evaluator.
 *
 * The user uploads a `.xlsx` matching
 * `code/inputs/RideYourWay_Prospective_Market_Intake_Example.xlsx`. The
 * backend merges the intake's prospective contracts onto the Q1 historical
 * baseline and returns a full viability payload (gates + readiness + ML).
 */
import type { GateRow, ViabilityLike } from "~/composables/viabilityDashboard"
import { gatesFromViability } from "~/composables/viabilityDashboard"

const { role } = useBackendApi()

interface JobStep {
  id: string
  label: string
  status: string
  detail?: string
  ts?: string
}

interface ProspectiveContract {
  name: string
  contract_type: string
  estimated_daily_rides: number
  estimated_revenue_per_trip: number
  order_modes: string[]
  noshow_billing_tier: string
  payer_name?: string
}

interface IntakeResult {
  viability: ViabilityLike & {
    readiness_state?: string
    readiness_reason?: string
    confidence_tier?: string
    ml_readiness?: {
      prediction?: string
      probability_ready?: number
      model_version?: string
      top_drivers?: Array<{ feature: string; impact: number }>
      error?: string
    }
  }
  intake: {
    organization: Record<string, string>
    prospective_contracts: ProspectiveContract[]
  }
}

const uploadBusy = ref(false)
const uploadError = ref("")
const uploadFileName = ref("")
const jobSteps = ref<JobStep[]>([])
const result = ref<IntakeResult | null>(null)

const requiredSheets: Array<{ name: string; tooltip: string }> = [
  {
    name: "Organization Intake",
    tooltip:
      "Label / value block describing the organization, primary payer, data period, and per-mode reference pricing."
  },
  {
    name: "Trip Demand Input",
    tooltip:
      "One row per program × trip mode: weekly completed trips, average revenue, acuity flag. Each row becomes a prospective contract."
  }
]

async function runIntakePipeline(file: File | null) {
  if (!file) return
  uploadFileName.value = file.name
  uploadError.value = ""
  jobSteps.value = []
  result.value = null
  uploadBusy.value = true
  try {
    const fd = new FormData()
    fd.append("file", file)
    const start = await $fetch<{ data: { job_id: string } }>("/api/jobs/intake-upload", {
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
        data: { status: string; steps: JobStep[]; error?: string; result?: IntakeResult }
      }>(`/api/backend/api/v1/jobs/${jobId}`, {
        headers: { "X-Role": role.value },
        timeout: 30_000
      })
      jobSteps.value = [...st.data.steps]
      if (st.data.status === "completed" && st.data.result) {
        result.value = st.data.result
        finished = true
      } else if (st.data.status === "failed") {
        uploadError.value = st.data.error || "Intake evaluation failed."
        finished = true
      } else {
        await new Promise((r) => setTimeout(r, 500))
      }
    }
    if (!finished && Date.now() >= deadline) {
      uploadError.value = "Evaluation timed out. Check server logs and workbook size."
    }
  } catch (e: unknown) {
    const err = e as { data?: { detail?: { message?: string } }; message?: string }
    uploadError.value = err?.data?.detail?.message ?? err?.message ?? "Upload failed."
  } finally {
    uploadBusy.value = false
  }
}

function reset() {
  uploadFileName.value = ""
  uploadError.value = ""
  jobSteps.value = []
  result.value = null
}

const gateRows = computed<GateRow[]>(() => {
  if (!result.value) return []
  return gatesFromViability(result.value.viability, [])
})

const selectedGateIndex = ref(0)
const selectedGate = computed(() => gateRows.value[selectedGateIndex.value])
function onGateSelected(idx: number) {
  selectedGateIndex.value = idx
}
watch(result, () => {
  selectedGateIndex.value = 0
})

const mlBlock = computed(() => result.value?.viability?.ml_readiness)
const pReady = computed(() => {
  const p = mlBlock.value?.probability_ready
  return typeof p === "number" ? p.toFixed(3) : "—"
})

const organization = computed(() => result.value?.intake.organization ?? {})
const contracts = computed(() => result.value?.intake.prospective_contracts ?? [])

function humanizeMode(mode: string): string {
  if (mode === "stretcher" || mode === "stretcher_alt") return "Stretcher"
  if (mode === "securecare") return "SecureCare"
  if (!mode) return "—"
  return mode.charAt(0).toUpperCase() + mode.slice(1)
}
</script>

<template>
  <div id="main-content" class="market-page" tabindex="-1">
    <PageHero
      eyebrow="Prospective market"
      subtitle="Upload an intake workbook · get a readiness call"
      title="Evaluate a prospective market"
      description="Drop a Prospective Market Intake `.xlsx`. The backend reads your Organization Intake and Trip Demand rows, rolls them into prospective contracts, runs them against the Q1 2026 historical baseline, and returns the same gates + XGBoost verdict you see on the dashboard."
    />

    <section v-if="!result" class="market-panel" aria-labelledby="intake-upload-title">
      <h2 id="intake-upload-title" class="market-panel__title">
        One intake workbook
        <InfoTip
          label="What we do with the upload"
          content="The file stays on the server. We extract the two required sheets, map each trip-demand row to a prospective contract, merge them onto the Q1 historical baseline, run the nine launch gates, and score XGBoost readiness. Total runtime is usually under a few seconds."
        />
      </h2>

      <ol class="upload-steps">
        <li class="upload-steps__item">
          <span class="upload-steps__num">1</span>
          <div class="upload-steps__body">
            <h3>Required sheets</h3>
            <p class="upload-steps__hint">Your workbook must contain these two sheet names exactly:</p>
            <ul class="sheet-chips" aria-label="Required sheet names">
              <li v-for="s in requiredSheets" :key="s.name" class="sheet-chip">
                <span class="sheet-chip__name">{{ s.name }}</span>
                <InfoTip :label="s.name" :content="s.tooltip" placement="bottom" />
              </li>
            </ul>
            <p class="upload-steps__ref">
              Reference shape:
              <code>code/inputs/RideYourWay_Prospective_Market_Intake_Example.xlsx</code>.
            </p>
          </div>
        </li>

        <li class="upload-steps__item">
          <span class="upload-steps__num">2</span>
          <div class="upload-steps__body">
            <h3>Drop the file</h3>
            <FileDropZone
              accept=".xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
              accept-label="XLSX"
              :disabled="uploadBusy"
              headline="Click to upload or drag and drop"
              hint="One intake workbook · we'll extract → map to contracts → merge with Q1 → run gates + XGBoost."
              :file-name="uploadFileName"
              @file-picked="runIntakePipeline"
            />
            <p v-if="uploadBusy" class="muted-note" aria-live="polite">Evaluating…</p>
            <p v-if="uploadError" class="error-text" role="alert">{{ uploadError }}</p>
          </div>
        </li>

        <li v-if="jobSteps.length" class="upload-steps__item">
          <span class="upload-steps__num">3</span>
          <div class="upload-steps__body">
            <h3>Pipeline progress</h3>
            <ol class="job-steps" aria-label="Pipeline progress">
              <li
                v-for="(s, idx) in jobSteps"
                :key="`${s.id}-${idx}-${s.ts || ''}`"
                :class="['job-step', `job-step--${s.status}`]"
              >
                <span class="job-step__label">{{ s.label }}</span>
                <span v-if="s.detail" class="job-step__detail">{{ s.detail }}</span>
              </li>
            </ol>
          </div>
        </li>
      </ol>
    </section>

    <section v-else class="result-stack" aria-label="Readiness result">
      <article class="market-panel result-summary">
        <div class="result-summary__head">
          <div>
            <div class="panel-eyebrow">Readiness call</div>
            <h2 class="result-summary__title">
              {{ result.viability.readiness_state ?? "—" }}
              <span class="result-summary__tier">{{ result.viability.confidence_tier ?? "" }}</span>
            </h2>
            <p class="result-summary__reason">{{ result.viability.readiness_reason }}</p>
            <p class="result-summary__meta">
              <strong>Market:</strong> {{ organization.organization_name || organization.contract_payer_name || uploadFileName }}
              <template v-if="organization.primary_service_area_market">
                · {{ organization.primary_service_area_market }}
              </template>
            </p>
          </div>
          <div class="result-summary__actions">
            <button type="button" class="secondary-button" @click="reset">Evaluate another market</button>
          </div>
        </div>

        <div v-if="mlBlock?.prediction" class="ml-box" aria-label="XGBoost prediction">
          <div class="ml-box__head">
            <span class="ml-box__title">XGBoost prediction</span>
            <InfoTip
              label="What this score means"
              content="Trained on real RYW operating history, the XGBoost classifier returns p(Ready). The readiness call above combines this probability with the nine-gate verdict."
            />
          </div>
          <div class="ml-box__row">
            <span class="ml-box__prediction" :data-state="mlBlock.prediction">{{ mlBlock.prediction }}</span>
            <span class="ml-box__p">p(Ready) = {{ pReady }}</span>
            <span v-if="mlBlock.model_version" class="ml-box__model">{{ mlBlock.model_version }}</span>
          </div>
          <ul v-if="mlBlock.top_drivers?.length" class="ml-box__drivers">
            <li v-for="(d, i) in mlBlock.top_drivers" :key="i">
              <span class="ml-box__driver-name">{{ d.feature }}</span>
              <span class="ml-box__driver-impact">impact {{ Number(d.impact).toFixed(4) }}</span>
            </li>
          </ul>
          <p v-else-if="mlBlock.error" class="muted-note">ML unavailable: {{ mlBlock.error }}</p>
        </div>
      </article>

      <article class="market-panel">
        <div class="panel-head">
          <div>
            <div class="panel-eyebrow">Launch readiness gate scorecard</div>
            <h2 class="panel-title">Nine gates evaluated on Q1 × your intake</h2>
          </div>
          <InfoTip
            label="How the gates work"
            content="Each gate encodes a launch-readiness condition (utilization, billed utilization, revenue density, etc.). Pass / fail is computed by the engine; confidence tiers mark which gates rely on assumption-backed fallbacks."
          />
        </div>
        <div class="gate-stack">
          <GateScorecard :rows="gateRows" :compact="true" @gate-selected="onGateSelected" />
          <GateDetailPanel
            :row="selectedGate"
            :index="selectedGateIndex"
            :total-count="gateRows.length"
          />
        </div>
      </article>

      <article class="market-panel">
        <div class="panel-head">
          <div>
            <div class="panel-eyebrow">Prospective contracts derived from intake</div>
            <h2 class="panel-title">{{ contracts.length }} contract{{ contracts.length === 1 ? "" : "s" }} mapped</h2>
          </div>
          <InfoTip
            label="How intake rows become contracts"
            content="Each Trip Demand Input row becomes one prospective contract: completed-trips-per-week ÷ 7 feeds estimated daily rides, the mode maps to an order mode, and organization-type flows into the no-show billing tier."
          />
        </div>
        <div class="contract-table-wrap">
          <table class="contract-table">
            <thead>
              <tr>
                <th scope="col">Program</th>
                <th scope="col">Mode</th>
                <th scope="col">Type</th>
                <th scope="col" class="num">Daily rides</th>
                <th scope="col" class="num">Rev / trip</th>
                <th scope="col">Payer</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(c, i) in contracts" :key="`${c.name}-${i}`">
                <td>{{ c.name }}</td>
                <td>{{ humanizeMode(c.order_modes[0] ?? "") }}</td>
                <td>{{ c.contract_type }}</td>
                <td class="num">{{ c.estimated_daily_rides.toFixed(1) }}</td>
                <td class="num">${{ c.estimated_revenue_per_trip.toFixed(2) }}</td>
                <td>{{ c.payer_name || "—" }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </article>
    </section>
  </div>
</template>

<style scoped>
.market-page {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.market-panel {
  padding: 22px 26px;
}
.market-panel__title {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 14px;
  font-size: clamp(1.1rem, 1.6vw, 1.35rem);
  letter-spacing: -0.02em;
}

.upload-steps {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 18px;
}
.upload-steps__item {
  display: grid;
  grid-template-columns: 34px 1fr;
  gap: 14px;
  align-items: flex-start;
}
.upload-steps__num {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  border-radius: 999px;
  background: var(--blue-soft);
  color: var(--blue);
  font-weight: 800;
  font-size: 0.95rem;
  margin-top: 2px;
}
.upload-steps__body h3 {
  margin: 0 0 4px;
  font-size: 0.98rem;
  letter-spacing: -0.01em;
}
.upload-steps__hint {
  margin: 0 0 8px;
  color: var(--muted);
  font-size: 0.88rem;
  line-height: 1.5;
}
.upload-steps__ref {
  margin: 8px 0 0;
  color: var(--muted);
  font-size: 0.82rem;
}
.upload-steps__ref code {
  font-size: 0.82em;
  background: var(--surface-2);
  border: 1px solid var(--line);
  padding: 1px 6px;
  border-radius: 6px;
}

.sheet-chips {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.sheet-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 999px;
  background: var(--surface-2);
  border: 1px solid var(--line);
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--ink);
}
.sheet-chip__name { font-variant-numeric: tabular-nums; }

.job-steps {
  margin: 0.5rem 0 0;
  padding-left: 1.25rem;
  max-width: 48rem;
}
.job-step {
  margin-bottom: 0.35rem;
  font-size: 0.9rem;
}
.job-step--running { color: var(--blue); font-weight: 600; }
.job-step--completed { color: var(--teal); }
.job-step--failed { color: var(--red); }
.job-step__detail {
  display: block;
  font-size: 0.85rem;
  color: var(--muted);
}

.muted-note {
  margin-top: 0.6rem;
  font-size: 0.9rem;
  color: var(--muted);
  max-width: 56rem;
  line-height: 1.55;
}

.result-stack {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.result-summary__head {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  justify-content: space-between;
  align-items: flex-start;
}
.result-summary__title {
  margin: 4px 0;
  font-size: clamp(1.4rem, 2.5vw, 1.9rem);
  letter-spacing: -0.03em;
}
.result-summary__tier {
  font-size: 0.78rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--muted);
  margin-left: 8px;
  vertical-align: middle;
}
.result-summary__reason {
  margin: 4px 0 0;
  max-width: 72ch;
  color: var(--ink);
  line-height: 1.55;
}
.result-summary__meta {
  margin-top: 6px;
  color: var(--muted);
  font-size: 0.88rem;
}
.result-summary__actions {
  display: flex;
  gap: 8px;
}
.secondary-button {
  appearance: none;
  border: 1px solid var(--line);
  background: var(--surface);
  color: var(--blue);
  padding: 8px 14px;
  border-radius: 10px;
  font-weight: 700;
  cursor: pointer;
  font-size: 0.88rem;
  transition: background 140ms ease, color 140ms ease;
}
.secondary-button:hover { background: var(--blue-soft); }

.ml-box {
  margin-top: 18px;
  padding: 14px 16px;
  border-radius: 14px;
  border: 1px solid var(--line);
  background: var(--surface-2);
}
.ml-box__head {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
.ml-box__title {
  font-weight: 800;
  letter-spacing: -0.02em;
}
.ml-box__row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px 16px;
  align-items: baseline;
}
.ml-box__prediction {
  font-weight: 800;
  padding: 2px 10px;
  border-radius: 999px;
  background: var(--surface);
  border: 1px solid var(--line);
}
.ml-box__prediction[data-state="Ready"] {
  color: var(--teal);
  border-color: var(--teal);
  background: color-mix(in srgb, var(--teal) 12%, transparent);
}
.ml-box__prediction[data-state="Not Ready"] {
  color: var(--red);
  border-color: var(--red);
  background: color-mix(in srgb, var(--red) 12%, transparent);
}
.ml-box__p {
  font-variant-numeric: tabular-nums;
  font-weight: 700;
}
.ml-box__model {
  color: var(--muted);
  font-size: 0.82rem;
}
.ml-box__drivers {
  margin: 10px 0 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 0.88rem;
}
.ml-box__drivers li {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 4px 0;
  border-bottom: 1px dashed var(--line);
}
.ml-box__drivers li:last-child { border-bottom: 0; }
.ml-box__driver-name { color: var(--ink); font-weight: 600; }
.ml-box__driver-impact {
  color: var(--muted);
  font-variant-numeric: tabular-nums;
}

.panel-head {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: space-between;
  align-items: flex-end;
  margin-bottom: 12px;
}
.panel-title {
  margin: 4px 0 0;
  font-size: clamp(1rem, 1.5vw, 1.2rem);
  letter-spacing: -0.02em;
}

.gate-stack {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.contract-table-wrap {
  overflow-x: auto;
  border: 1px solid var(--line);
  border-radius: 12px;
}
.contract-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.88rem;
}
.contract-table th,
.contract-table td {
  padding: 8px 12px;
  border-bottom: 1px solid var(--line);
  text-align: left;
}
.contract-table thead th {
  background: var(--surface-2);
  font-weight: 700;
  color: var(--ink);
  font-size: 0.78rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.contract-table tbody tr:last-child td { border-bottom: 0; }
.contract-table .num {
  text-align: right;
  font-variant-numeric: tabular-nums;
}
</style>
