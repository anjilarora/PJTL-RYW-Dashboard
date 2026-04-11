<script setup lang="ts">
defineProps<{
  actions: Array<{ owner: string; title: string; detail: string; due: string; status: string }>
}>()

function statusClass(status: string): string {
  const s = status.toLowerCase()
  if (s.includes("progress")) return "is-progress"
  if (s.includes("done") || s.includes("complete")) return "is-done"
  if (s.includes("block")) return "is-blocked"
  return "is-neutral"
}
</script>

<template>
  <article class="panel">
    <div class="panel-eyebrow">
      Risk and Mitigation
      <InfoTip
        label="About the execution queue"
        content="These are the owner-assigned actions required to flip the failing and provisional gates. Click a row to see the full description, the owner, and the due date. Closing every action here is how the market moves from No-Go to Go-for-Launch."
      />
    </div>
    <h2>Execution Queue</h2>
    <p class="queue-lead">
      {{ actions.length }} open actions. Expand each row to see the owner, the due date, and what has to happen before the gate can close.
    </p>
    <div class="queue-list">
      <CollapsibleCard
        v-for="action in actions"
        :key="action.title"
        :title="action.title"
        :summary="`${action.owner} · due ${action.due}`"
      >
        <div class="queue-meta">
          <span class="table-badge is-owner">{{ action.owner }}</span>
          <span class="status-chip status-chip--compact" :class="statusClass(action.status)">{{ action.status }}</span>
          <span class="queue-due">Due: {{ action.due }}</span>
        </div>
        <p class="queue-detail">{{ action.detail }}</p>
      </CollapsibleCard>
    </div>
  </article>
</template>

<style scoped>
.queue-lead {
  margin: 6px 0 14px;
  color: var(--ink);
  line-height: 1.55;
  max-width: 62ch;
}
.queue-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.queue-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 12px;
  align-items: center;
  margin: 6px 0 8px;
}
.queue-due {
  font-size: 0.85rem;
  color: var(--muted);
  font-variant-numeric: tabular-nums;
}
.queue-detail {
  margin: 4px 0 0;
  color: var(--ink);
  line-height: 1.55;
}
.panel-eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
</style>
