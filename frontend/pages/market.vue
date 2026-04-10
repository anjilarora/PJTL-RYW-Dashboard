<script setup lang="ts">
import { RYW_STORAGE_HISTORICAL, RYW_STORAGE_MARKET } from "~/composables/useViabilitySession"

const { role, lastError, apiPost } = useBackendApi()

const regionName = ref("Grand Rapids North Corridor")
const regionState = ref("MI")
const fleet = ref({
  wheelchair_vehicles: 2,
  ambulatory_vehicles: 2,
  stretcher_vehicles: 1,
  securecare_vehicles: 1,
  drivers: 8
})
const overbookingLimit = ref(1.2)
const brokerVolumePct = ref(0.3)
const prospectiveJson = ref("[]")
const historicalJson = ref("{}")

const parseError = ref("")
const pageError = ref("")
const result = ref<any>(null)
const fileHint = ref("")

function buildMarketProfile() {
  let prospective_contracts: unknown[] = []
  try {
    const parsed = JSON.parse(prospectiveJson.value || "[]")
    if (!Array.isArray(parsed)) throw new Error("prospective_contracts must be a JSON array")
    prospective_contracts = parsed
  } catch (e: any) {
    throw new Error(`Prospective contracts JSON: ${e?.message ?? "invalid"}`)
  }
  return {
    region: { region_name: regionName.value.trim(), state: regionState.value.trim() },
    fleet: {
      wheelchair_vehicles: Number(fleet.value.wheelchair_vehicles) || 0,
      ambulatory_vehicles: Number(fleet.value.ambulatory_vehicles) || 0,
      stretcher_vehicles: Number(fleet.value.stretcher_vehicles) || 0,
      securecare_vehicles: Number(fleet.value.securecare_vehicles) || 0,
      drivers: Number(fleet.value.drivers) || 0
    },
    overbooking_limit: Number(overbookingLimit.value) || 1.2,
    broker_volume_pct: (() => {
      const v = Number(brokerVolumePct.value)
      return Number.isFinite(v) ? v : 0.3
    })(),
    prospective_contracts
  }
}

function parseHistorical(): Record<string, unknown> {
  const raw = historicalJson.value.trim()
  if (!raw) return {}
  try {
    const o = JSON.parse(raw)
    if (o === null || typeof o !== "object" || Array.isArray(o)) {
      throw new Error("historical_data must be a JSON object")
    }
    return o as Record<string, unknown>
  } catch (e: any) {
    throw new Error(`Historical JSON: ${e?.message ?? "invalid"}`)
  }
}

function persistToSession() {
  parseError.value = ""
  try {
    const market_profile = buildMarketProfile()
    const historical_data = parseHistorical()
    sessionStorage.setItem(RYW_STORAGE_MARKET, JSON.stringify(market_profile))
    sessionStorage.setItem(RYW_STORAGE_HISTORICAL, JSON.stringify(historical_data))
    fileHint.value = "Saved to browser session. Dashboard readiness run will use this payload."
  } catch (e: any) {
    parseError.value = e?.message ?? "Validation failed"
    fileHint.value = ""
  }
}

async function runEvaluation() {
  pageError.value = ""
  result.value = null
  parseError.value = ""
  try {
    const market_profile = buildMarketProfile()
    const historical_data = parseHistorical()
    sessionStorage.setItem(RYW_STORAGE_MARKET, JSON.stringify(market_profile))
    sessionStorage.setItem(RYW_STORAGE_HISTORICAL, JSON.stringify(historical_data))
    const res = await apiPost<any>("/api/backend/api/v1/viability/evaluate", {
      market_profile,
      historical_data
    })
    result.value = res.data
    fileHint.value = "Evaluated and saved payload to session."
  } catch (e: any) {
    pageError.value = lastError.value?.message ?? e?.message ?? "Evaluation failed"
  }
}

function onHistoricalFile(ev: Event) {
  parseError.value = ""
  const input = ev.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = () => {
    try {
      const text = String(reader.result ?? "")
      const o = JSON.parse(text)
      if (o === null || typeof o !== "object" || Array.isArray(o)) {
        parseError.value = "File must contain a JSON object for historical_data"
        return
      }
      historicalJson.value = JSON.stringify(o, null, 2)
      fileHint.value = `Loaded historical data from ${file.name}`
    } catch {
      parseError.value = "Could not parse JSON from file"
    }
  }
  reader.readAsText(file)
  input.value = ""
}

onMounted(() => {
  try {
    const m = sessionStorage.getItem(RYW_STORAGE_MARKET)
    if (m) {
      const mp = JSON.parse(m)
      regionName.value = mp.region?.region_name ?? regionName.value
      regionState.value = mp.region?.state ?? regionState.value
      if (mp.fleet) fleet.value = { ...fleet.value, ...mp.fleet }
      if (mp.overbooking_limit != null) overbookingLimit.value = mp.overbooking_limit
      if (mp.broker_volume_pct != null) brokerVolumePct.value = mp.broker_volume_pct
      if (Array.isArray(mp.prospective_contracts)) {
        prospectiveJson.value = JSON.stringify(mp.prospective_contracts, null, 2)
      }
    }
    const h = sessionStorage.getItem(RYW_STORAGE_HISTORICAL)
    if (h) historicalJson.value = JSON.stringify(JSON.parse(h), null, 2)
  } catch {
    /* ignore */
  }
})
</script>

<template>
  <div id="main-content" class="market-page" tabindex="-1">
    <PageHero
      eyebrow="Market intake"
      subtitle="Payload builder"
      title="Market & readiness"
      description="Build the viability payload (market profile + historical data) that the dashboard's readiness run will use. Requires the analyst role (or higher) to evaluate."
    />

    <section class="market-panel">
        <h2>Market profile</h2>
        <div class="form-grid">
          <label>Region name <input v-model="regionName" type="text" class="form-field" /></label>
          <label>State <input v-model="regionState" type="text" class="form-field" /></label>
          <label>Wheelchair vehicles <input v-model.number="fleet.wheelchair_vehicles" type="number" min="0" class="form-field" /></label>
          <label>Ambulatory vehicles <input v-model.number="fleet.ambulatory_vehicles" type="number" min="0" class="form-field" /></label>
          <label>Stretcher vehicles <input v-model.number="fleet.stretcher_vehicles" type="number" min="0" class="form-field" /></label>
          <label>Securecare vehicles <input v-model.number="fleet.securecare_vehicles" type="number" min="0" class="form-field" /></label>
          <label>Drivers <input v-model.number="fleet.drivers" type="number" min="0" class="form-field" /></label>
          <label>Overbooking limit <input v-model.number="overbookingLimit" type="number" step="0.05" min="0" class="form-field" /></label>
          <label>Broker volume % <input v-model.number="brokerVolumePct" type="number" step="0.05" min="0" max="1" class="form-field" /></label>
        </div>
        <label class="block-label">Prospective contracts (JSON array)</label>
        <textarea v-model="prospectiveJson" class="form-field form-field--textarea" rows="6" spellcheck="false" />

        <h2>Historical data</h2>
        <p class="market-hint">Paste a JSON <strong>object</strong> (e.g. <code>baselines</code>, <code>contracts</code>) or load from file.</p>
        <label class="file-label">
          Load from file
          <input type="file" accept=".json,application/json" class="file-input" @change="onHistoricalFile" />
        </label>
        <textarea v-model="historicalJson" class="form-field form-field--textarea" rows="10" spellcheck="false" placeholder="{}" />

        <p v-if="parseError" class="error-text" role="alert">{{ parseError }}</p>
        <p v-if="pageError" class="error-text" role="alert">{{ pageError }}</p>
        <p v-if="fileHint" class="market-ok-text">{{ fileHint }}</p>

        <div class="actions">
          <button type="button" class="secondary-button" @click="persistToSession">Save payload to session only</button>
          <button type="button" class="primary-button" @click="runEvaluation">Run readiness evaluation</button>
        </div>
      </section>

      <section v-if="result" class="market-panel">
        <h2>Result</h2>
        <p>
          <strong>{{ result.readiness_state }}</strong> · {{ result.confidence_tier }}
        </p>
        <p class="reason">{{ result.readiness_reason }}</p>
        <div v-if="result.ml_readiness?.prediction" class="market-ml-box">
          <h3>ML readiness</h3>
          <p>
            {{ result.ml_readiness.prediction }} · p(Ready)={{ Number(result.ml_readiness.probability_ready).toFixed(3) }} ·
            {{ result.ml_readiness.model_version }}
          </p>
          <ul v-if="result.ml_readiness.top_drivers?.length">
            <li v-for="(d, i) in result.ml_readiness.top_drivers" :key="i">
              {{ d.feature }}: impact={{ Number(d.impact).toFixed(4) }}
            </li>
          </ul>
        </div>
      </section>
  </div>
</template>

<style scoped>
.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(min(100%, 200px), 1fr));
  gap: 0.75rem;
  margin-bottom: 1rem;
}
label {
  font-size: 0.85rem;
  display: block;
  color: var(--ink);
}
.block-label {
  margin-top: 0.5rem;
  color: var(--ink);
}
.file-label {
  display: inline-block;
  margin: 0.5rem 0;
  font-size: 0.9rem;
  color: var(--muted);
}
.file-input {
  display: block;
  margin-top: 0.25rem;
}
.actions {
  margin-top: 1rem;
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}
.reason {
  font-size: 0.95rem;
  max-width: 50rem;
  color: var(--muted);
  line-height: 1.55;
}
</style>
