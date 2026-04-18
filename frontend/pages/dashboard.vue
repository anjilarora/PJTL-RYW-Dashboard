<script setup lang="ts">
/**
 * Dashboard – Q1 2026 baseline view.
 *
 * The dashboard no longer accepts uploads. On mount it fetches the cached
 * viability payload produced by `GET /api/v1/viability/baseline` (computed
 * once from the bundled Q1 Daily Metrics workbook) and maps it onto the
 * dashboard scaffold. The prospective-intake / XGBoost evaluation flow now
 * lives on `/market`.
 */
import { gatesFromViability, marketFromViability, readinessFromViability } from "~/composables/viabilityDashboard"

const { data } = await useFetch("/api/dashboard")
const { apiGet } = useBackendApi()

const viability = ref<unknown>(null)
const baselineError = ref("")
const baselineLoading = ref(false)

async function loadBaseline() {
  baselineLoading.value = true
  baselineError.value = ""
  try {
    const envelope = await apiGet<unknown>("/api/backend/api/v1/viability/baseline")
    viability.value = (envelope as { data?: unknown })?.data ?? null
  } catch (exc: unknown) {
    const err = exc as { data?: { error?: { message?: string } }; message?: string }
    baselineError.value = err?.data?.error?.message ?? err?.message ?? "Could not load the Q1 baseline."
  } finally {
    baselineLoading.value = false
  }
}

onMounted(() => {
  loadBaseline()
})

const displayMarket = computed(() => {
  if (!data.value) return { name: "", summary: "", status: "", confidence: "", corridor: "", cityState: "" }
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
  if (!(viability.value as any)?.report?.conditions?.length) return d.readiness
  return readinessFromViability(viability.value, d.readiness)
})

type TabId = "snapshot" | "gates" | "intake" | "ops" | "execution"
const activeDetailTab = ref<TabId>("snapshot")
const detailTabs: Array<{ id: TabId; label: string }> = [
  { id: "snapshot", label: "Operating snapshot" },
  { id: "gates", label: "Gate readiness" },
  { id: "intake", label: "Intake & programs" },
  { id: "ops", label: "Operational deep dive" },
  { id: "execution", label: "Execution queue" }
]

const fleetScorecard = useFleetScorecard()
const weeklyTrend = useWeeklyTrend()
const modeProfitability = useModeProfitability()
const otpMatrix = useOtpMatrix()
const payerConcentration = usePayerConcentration()
const hourlyDemand = useHourlyDemand()
const cancellations = useCancellations()
const revPerKl = useRevPerKentleg()
const secureCare = useSecureCareCompare()
const regionalCost = useRegionalCost()

const opsLoaders = [
  fleetScorecard,
  weeklyTrend,
  modeProfitability,
  otpMatrix,
  payerConcentration,
  hourlyDemand,
  cancellations,
  revPerKl,
  secureCare,
  regionalCost
]

type OpsId = "d1" | "d2" | "d3" | "d4" | "d5" | "d6" | "d7" | "d8" | "d9" | "d10"
const opsSubTabs: Array<{ id: OpsId; num: string; label: string; info: string }> = [
  { id: "d1", num: "D1", label: "Regional scorecard", info: "Nine gates × 3 regions with pass / fail verdict." },
  { id: "d2", num: "D2", label: "Weekly trend", info: "Week-over-week movement for every gate." },
  { id: "d3", num: "D3", label: "Mode mix", info: "Revenue, margin and no-show by transport mode." },
  { id: "d4", num: "D4", label: "OTP matrix", info: "On-time performance heatmap by region × weekday." },
  { id: "d5", num: "D5", label: "Payer concentration", info: "Distance from the 20% cap, per payer." },
  { id: "d6", num: "D6", label: "Hourly demand", info: "24×7 demand / idle heatmap with biggest gaps." },
  { id: "d7", num: "D7", label: "Cancellations", info: "Who / when / why trips drop off." },
  { id: "d8", num: "D8", label: "Rev / Kent-Leg", info: "Which payers lift vs drag the $70 target." },
  { id: "d9", num: "D9", label: "SecureCare vs base", info: "SecureCare P&L compared to the base fleet." },
  { id: "d10", num: "D10", label: "Regional cost", info: "Apportioned cost-per-road-hour (estimate)." }
]
const activeOpsTab = ref<OpsId>("d1")

watch(activeDetailTab, (tab) => {
  if (tab === "ops") {
    for (const loader of opsLoaders) loader.load()
  }
})

onMounted(() => {
  for (const loader of opsLoaders) loader.load()
})

const selectedGateIndex = ref(0)
const selectedGate = computed(() => displayGates.value[selectedGateIndex.value])

function onGateSelected(idx: number) {
  selectedGateIndex.value = idx
}
</script>

<template>
  <div id="main-content" tabindex="-1">
    <div v-if="data">
      <MarketHero
        :name="displayMarket.name"
        :city-state="displayMarket.cityState"
        :corridor="displayMarket.corridor"
        :status="displayMarket.status"
        :confidence="displayMarket.confidence"
        :summary="displayMarket.summary"
        :readiness="displayReadiness"
      />

      <div class="source-strip" role="status" aria-live="polite">
        <span class="source-strip__dot" aria-hidden="true" />
        <span class="source-strip__label">Q1 2026 reference data</span>
        <span class="source-strip__short">
          Every panel on this page reflects the January–March 2026 operating numbers for this corridor.
        </span>
        <InfoTip
          label="Where these numbers come from"
          content="The dashboard shows the Q1 2026 results for the Grand Rapids corridor. To score a different market, open Market Readiness and upload an intake workbook."
          placement="bottom"
        />
        <NuxtLink to="/market" class="source-strip__cta">Score a new market</NuxtLink>
      </div>

      <p v-if="baselineLoading" class="muted-note" aria-live="polite">Loading Q1 baseline…</p>
      <p v-if="baselineError" class="error-text" role="alert">{{ baselineError }}</p>

      <section class="detail-tabs" aria-label="Dashboard sections">
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
          v-show="activeDetailTab === 'snapshot'"
          id="detail-panel-snapshot"
          role="tabpanel"
          aria-labelledby="detail-tab-snapshot"
        >
          <KpiSnapshotPanel
            :readiness="displayReadiness"
            :prospective="data.prospective"
            source="upload"
          />
        </div>

        <div
          v-show="activeDetailTab === 'gates'"
          id="detail-panel-gates"
          role="tabpanel"
          aria-labelledby="detail-tab-gates"
          class="panel-stack"
        >
          <GateScorecard :rows="displayGates" @gate-selected="onGateSelected" />
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
          v-show="activeDetailTab === 'ops'"
          id="detail-panel-ops"
          role="tabpanel"
          aria-labelledby="detail-tab-ops"
        >
          <div class="ops-header">
            <div>
              <div class="panel-eyebrow">
                Operational deep dive
                <InfoTip
                  label="How to use this tab"
                  content="Ten mini-dashboards built directly from the Q1 2026 operating workbooks. Pick any pill to jump to one deep dive; the title and info chip on each panel explains what you're looking at."
                />
              </div>
              <h2 class="ops-title">Deep dives · D1 through D10</h2>
              <p class="ops-subtitle">{{ opsSubTabs.find(o => o.id === activeOpsTab)?.info }}</p>
            </div>
          </div>

          <nav class="ops-subtabs" role="tablist" aria-label="Operational deep-dive sections">
            <button
              v-for="s in opsSubTabs"
              :key="s.id"
              type="button"
              role="tab"
              :aria-selected="activeOpsTab === s.id"
              class="ops-subtab"
              :class="{ 'ops-subtab--active': activeOpsTab === s.id }"
              @click="activeOpsTab = s.id"
            >
              <span class="ops-subtab__num">{{ s.num }}</span>
              <span class="ops-subtab__label">{{ s.label }}</span>
            </button>
          </nav>

          <div class="ops-stage">
            <FleetScorecardPanel
              v-show="activeOpsTab === 'd1'"
              :regions="(fleetScorecard.data.value?.regions ?? []) as any"
              :loading="fleetScorecard.loading.value"
              :error="fleetScorecard.error.value"
            />
            <WeeklyTrendPanel
              v-show="activeOpsTab === 'd2'"
              :weeks="(weeklyTrend.data.value?.weeks ?? []) as any"
              :loading="weeklyTrend.loading.value"
              :error="weeklyTrend.error.value"
            />
            <ModeMixPanel
              v-show="activeOpsTab === 'd3'"
              :modes="(modeProfitability.data.value?.modes ?? []) as any"
              :loading="modeProfitability.loading.value"
              :error="modeProfitability.error.value"
            />
            <OtpMatrixPanel
              v-show="activeOpsTab === 'd4'"
              :rows="(otpMatrix.data.value?.rows ?? []) as any"
              :loading="otpMatrix.loading.value"
              :error="otpMatrix.error.value"
            />
            <PayerConcentrationPanel
              v-show="activeOpsTab === 'd5'"
              :payers="(payerConcentration.data.value?.payers ?? []) as any"
              :warnings="(payerConcentration.data.value?.warnings ?? []) as any"
              :cap-volume="payerConcentration.data.value?.cap_volume ?? 0.2"
              :cap-revenue="payerConcentration.data.value?.cap_revenue ?? 0.2"
              :loading="payerConcentration.loading.value"
              :error="payerConcentration.error.value"
            />
            <HourlyDemandPanel
              v-show="activeOpsTab === 'd6'"
              :rows="(hourlyDemand.data.value?.rows ?? []) as any"
              :idle-windows="(hourlyDemand.data.value?.idle_windows ?? []) as any"
              :loading="hourlyDemand.loading.value"
              :error="hourlyDemand.error.value"
            />
            <CancellationPanel
              v-show="activeOpsTab === 'd7'"
              :rows="(cancellations.data.value?.rows ?? []) as any"
              :by-reason="cancellations.data.value?.by_reason ?? []"
              :by-mode="cancellations.data.value?.by_mode ?? []"
              :by-day="cancellations.data.value?.by_day ?? []"
              :by-payer="cancellations.data.value?.by_payer ?? []"
              :total="cancellations.data.value?.total ?? 0"
              :loading="cancellations.loading.value"
              :error="cancellations.error.value"
            />
            <RevPerKentlegPanel
              v-show="activeOpsTab === 'd8'"
              :payers="(revPerKl.data.value?.payers ?? []) as any"
              :target="revPerKl.data.value?.target ?? 70"
              :fleet-rev-per-kentleg="revPerKl.data.value?.fleet_rev_per_kentleg ?? null"
              :loading="revPerKl.loading.value"
              :error="revPerKl.error.value"
            />
            <SecureCareComparePanel
              v-show="activeOpsTab === 'd9'"
              :streams="(secureCare.data.value?.streams ?? {}) as any"
              :loading="secureCare.loading.value"
              :error="secureCare.error.value"
            />
            <RegionalCostPanel
              v-show="activeOpsTab === 'd10'"
              :regions="(regionalCost.data.value?.regions ?? []) as any"
              :target-cost-per-road-hour="regionalCost.data.value?.target_cost_per_road_hour ?? 50"
              :is-estimate="regionalCost.data.value?.is_estimate ?? true"
              :loading="regionalCost.loading.value"
              :error="regionalCost.error.value"
            />
          </div>
        </div>

        <div
          v-show="activeDetailTab === 'execution'"
          id="detail-panel-execution"
          role="tabpanel"
          aria-labelledby="detail-tab-execution"
        >
          <RiskMitigationPanel :actions="data.riskActions" />
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.muted-note {
  margin-top: 0.6rem;
  font-size: 0.9rem;
  color: var(--muted);
  max-width: 56rem;
  line-height: 1.55;
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
  background: var(--teal);
  flex-shrink: 0;
}
.source-strip__label {
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  font-size: 0.7rem;
  color: var(--teal);
}
.source-strip__short {
  color: var(--ink);
  font-weight: 600;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1 1 220px;
}
.source-strip__short code {
  font-size: 0.82em;
  background: var(--surface);
  border: 1px solid var(--line);
  padding: 1px 6px;
  border-radius: 6px;
  font-weight: 500;
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
  text-decoration: none;
  transition: background 140ms ease, color 140ms ease;
}
.source-strip__cta:hover { background: var(--blue-soft); }

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
.detail-tabs__tab:hover { color: var(--ink); }
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

.panel-stack {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.ops-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 14px;
  margin-top: 4px;
  flex-wrap: wrap;
}
.ops-title {
  margin: 4px 0 0;
  font-size: clamp(1.1rem, 1.7vw, 1.4rem);
  letter-spacing: -0.03em;
}
.ops-subtitle {
  margin: 4px 0 0;
  color: var(--muted);
  max-width: 78ch;
}

.ops-subtabs {
  display: flex;
  gap: 6px;
  padding: 6px;
  margin: 10px 0 12px;
  border-radius: 14px;
  background: var(--surface-2);
  border: 1px solid var(--line);
  overflow-x: auto;
  scrollbar-width: thin;
}
.ops-subtab {
  appearance: none;
  border: 1px solid transparent;
  background: transparent;
  color: var(--muted);
  padding: 6px 10px;
  border-radius: 10px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  white-space: nowrap;
  transition: background 140ms ease, color 140ms ease, border-color 140ms ease;
}
.ops-subtab:hover { color: var(--ink); background: var(--surface); }
.ops-subtab--active {
  background: var(--surface);
  color: var(--blue);
  border-color: var(--blue);
  box-shadow: 0 2px 8px color-mix(in srgb, var(--blue) 18%, transparent);
}
.ops-subtab__num {
  font-weight: 800;
  font-size: 0.74rem;
  padding: 2px 6px;
  border-radius: 999px;
  background: var(--blue-soft);
  color: var(--blue);
  letter-spacing: 0.04em;
}
.ops-subtab--active .ops-subtab__num {
  background: var(--blue);
  color: var(--white);
}
.ops-subtab__label {
  font-size: 0.84rem;
  font-weight: 700;
}

.ops-stage {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
</style>
