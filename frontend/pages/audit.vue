<script setup lang="ts">
const { data } = await useFetch("/api/dashboard")
const { apiPost } = useBackendApi()
const trace = ref<any>(null)

async function loadTrace() {
  const res = await apiPost<any>("/api/backend/api/v1/viability/evaluate", {
    market_profile: {
      region: { region_name: "Audit Run", state: "MI" },
      fleet: { wheelchair_vehicles: 1, ambulatory_vehicles: 1, stretcher_vehicles: 1, securecare_vehicles: 0, drivers: 3 },
      prospective_contracts: []
    },
    historical_data: {}
  })
  trace.value = res.data
}
</script>

<template>
  <div id="main-content" tabindex="-1">
    <PageHero
      eyebrow="Audit"
      subtitle="Formula · confidence · lineage"
      title="Analyst Audit Mode"
      description="Reproducible trace for every readiness call: which formula ran, what confidence tier it earned, which inputs it read, and which source-of-truth document each value came from."
    />

    <section class="panel">
      <h2>Trace Run</h2>
      <button class="primary-button" @click="loadTrace">Generate Trace</button>
    </section>

    <AuditTraceabilityPanel :governance="trace?.governance" :lineage-refs="trace?.lineage_refs" />

    <section v-if="trace?.ml_readiness?.prediction" class="panel">
      <h2>ML readiness</h2>
      <p>
        <strong>{{ trace.ml_readiness.prediction }}</strong>
        · p(Ready)={{ Number(trace.ml_readiness.probability_ready).toFixed(3) }}
        · {{ trace.ml_readiness.model_version }}
      </p>
      <ul v-if="trace.ml_readiness.top_drivers?.length" class="driver-list">
        <li v-for="(d, i) in trace.ml_readiness.top_drivers" :key="i">
          {{ d.feature }}: impact={{ Number(d.impact).toFixed(4) }}
        </li>
      </ul>
    </section>

    <section v-if="trace?.gate_details" class="panel">
      <h2>Gate Details</h2>
      <pre>{{ trace?.gate_details }}</pre>
    </section>
  </div>
</template>

<style scoped>
.driver-list {
  margin: 0.5rem 0 0;
  padding-left: 1.25rem;
  font-size: 0.9rem;
}
</style>
