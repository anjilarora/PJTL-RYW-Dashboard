<script setup lang="ts">
const props = defineProps<{
  governance?: { authority_precedence?: string[]; confidence_framework?: string[]; phase_artifacts?: string[] }
  lineageRefs?: Record<string, string>
}>()

const authorityList = computed(() => props.governance?.authority_precedence ?? [])
const confidenceList = computed(() => props.governance?.confidence_framework ?? [])
const phaseList = computed(() => props.governance?.phase_artifacts ?? [])
const lineageEntries = computed(() => Object.entries(props.lineageRefs ?? {}))
const hasGovernance = computed(() =>
  authorityList.value.length + confidenceList.value.length + phaseList.value.length > 0
)
</script>

<template>
  <article class="panel">
    <div class="panel-eyebrow">
      Audit Traceability
      <InfoTip
        label="About source and formula trace"
        content="Every readiness call is tied back to the data and formulas that produced it. This block shows the authority precedence the engine used, the confidence framework that scored each gate, and - when available - the lineage reference IDs that point at the canonical source rows. It is here so that any decision can be reproduced from a clean checkout."
      />
    </div>
    <h2>Source and Formula Trace</h2>
    <p class="trace-lead">
      Use the sections below to see which rules and source rows produced the current readiness call. Expand the ones you want to audit.
    </p>

    <CollapsibleCard
      v-if="hasGovernance"
      title="Governance"
      summary="Authority, confidence, phase artifacts"
      :open="false"
    >
      <template v-if="authorityList.length">
        <h4 class="trace-subhead">Authority precedence</h4>
        <ol class="trace-list">
          <li v-for="item in authorityList" :key="item">{{ item }}</li>
        </ol>
      </template>
      <template v-if="confidenceList.length">
        <h4 class="trace-subhead">Confidence framework</h4>
        <ul class="trace-list">
          <li v-for="item in confidenceList" :key="item">{{ item }}</li>
        </ul>
      </template>
      <template v-if="phaseList.length">
        <h4 class="trace-subhead">Phase artifacts</h4>
        <ul class="trace-list">
          <li v-for="item in phaseList" :key="item">{{ item }}</li>
        </ul>
      </template>
    </CollapsibleCard>

    <CollapsibleCard
      title="Lineage references"
      :summary="lineageEntries.length ? `${lineageEntries.length} references` : 'none supplied'"
      :open="false"
    >
      <p v-if="!lineageEntries.length" class="trace-empty">
        No lineage references have been attached to the current readiness call. Lineage is populated once an audited pipeline runs end-to-end.
      </p>
      <dl v-else class="trace-dl">
        <template v-for="[key, value] in lineageEntries" :key="key">
          <dt>{{ key }}</dt>
          <dd>{{ value }}</dd>
        </template>
      </dl>
    </CollapsibleCard>
  </article>
</template>

<style scoped>
.trace-lead {
  margin: 6px 0 14px;
  color: var(--ink);
  line-height: 1.55;
  max-width: 62ch;
}
.trace-subhead {
  margin: 14px 0 6px;
  font-size: 0.82rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--muted);
}
.trace-list {
  margin: 0 0 10px;
  padding-left: 1.25rem;
  font-size: 0.92rem;
  line-height: 1.55;
  color: var(--ink);
}
.trace-list li + li {
  margin-top: 4px;
}
.trace-empty {
  color: var(--muted);
  margin: 0;
  font-size: 0.9rem;
}
.trace-dl {
  display: grid;
  grid-template-columns: minmax(140px, 14rem) 1fr;
  gap: 6px 16px;
  margin: 0;
  font-size: 0.9rem;
  line-height: 1.5;
}
.trace-dl dt {
  color: var(--muted);
  font-weight: 600;
}
.trace-dl dd {
  margin: 0;
  color: var(--ink);
  word-break: break-word;
}
.panel-eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

@media (max-width: 520px) {
  .trace-dl {
    grid-template-columns: 1fr;
    gap: 2px 0;
  }
  .trace-dl dt {
    margin-top: 8px;
  }
}
</style>
