<script setup lang="ts">
defineProps<{
  assumptions: Array<{ title: string; detail: string; source?: string }>
}>()
</script>

<template>
  <article class="panel">
    <div class="panel-eyebrow">
      Sensitivity and Scenarios
      <InfoTip
        label="About assumption branches"
        content="These are the inputs that are not yet pulled from audited data. Every bullet below is a knob that still flexes the readiness answer. Each branch lists what is currently assumed, why it is assumed, and what the team needs to do to lock it down. Expand each row to see the detail - once every branch is resolved the readiness output moves from Tier 2 / 3 toward Tier 1 Audited."
      />
    </div>
    <h2>Assumption Branches</h2>
    <p class="branches-lead">
      Every branch is a temporary input that can shift the readiness call. Open each one to see what is currently assumed and what still needs to be confirmed or replaced with audited data.
    </p>
    <div class="branches-list">
      <CollapsibleCard
        v-for="(item, idx) in assumptions"
        :key="item.title"
        :title="`${idx + 1}. ${item.title}`"
        :summary="item.source ? `Source: ${item.source}` : 'Open to review'"
      >
        <p>{{ item.detail }}</p>
        <p v-if="item.source" class="branches-source">
          <strong>Where it comes from:</strong>
          <code>{{ item.source }}</code>
        </p>
        <p class="branches-action">
          <strong>What to do:</strong>
          Replace this assumption with validated inputs once the source-of-truth formula is locked. Until then the readiness call depends on this value staying within its stated range.
        </p>
      </CollapsibleCard>
    </div>
  </article>
</template>

<style scoped>
.branches-lead {
  margin: 6px 0 14px;
  color: var(--ink);
  line-height: 1.55;
  max-width: 62ch;
}
.branches-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.branches-action {
  margin: 10px 0 0;
  padding: 10px 12px;
  border-radius: 8px;
  background: var(--surface-3);
  border-left: 3px solid var(--blue);
  color: var(--ink);
  font-size: 0.88rem;
  line-height: 1.5;
}
.branches-source {
  margin: 8px 0 0;
  font-size: 0.85rem;
  color: var(--muted);
}
.branches-source code {
  font-size: 0.82rem;
  background: var(--surface-3);
  padding: 1px 6px;
  border-radius: 6px;
  color: var(--ink);
  margin-left: 4px;
}
.panel-eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
</style>
