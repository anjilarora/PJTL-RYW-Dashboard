<script setup lang="ts">
withDefaults(
  defineProps<{
    title: string
    summary?: string
    open?: boolean
  }>(),
  { summary: "", open: false }
)
</script>

<template>
  <details class="accordion" :open="open">
    <summary class="accordion__summary">
      <span class="accordion__title">{{ title }}</span>
      <span v-if="summary" class="accordion__summary-meta">{{ summary }}</span>
      <span class="accordion__chevron" aria-hidden="true">
        <svg viewBox="0 0 12 12" width="12" height="12"><path d="M3 4.5l3 3 3-3" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
      </span>
    </summary>
    <div class="accordion__body">
      <slot />
    </div>
  </details>
</template>

<style scoped>
.accordion {
  border: 1px solid var(--line);
  border-radius: 12px;
  background: var(--surface-2);
  overflow: hidden;
  transition: border-color 150ms ease, box-shadow 150ms ease;
}

.accordion + .accordion {
  margin-top: 10px;
}

.accordion[open] {
  border-color: var(--line-strong);
  box-shadow: var(--shadow);
}

.accordion__summary {
  list-style: none;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 18px;
  cursor: pointer;
  user-select: none;
  font-weight: 600;
  color: var(--ink);
}

.accordion__summary::-webkit-details-marker {
  display: none;
}

.accordion__title {
  flex: 1 1 auto;
  min-width: 0;
  font-size: 0.98rem;
}

.accordion__summary-meta {
  flex: 0 0 auto;
  font-size: 0.82rem;
  font-weight: 500;
  color: var(--muted);
}

.accordion__chevron {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--muted);
  transition: transform 180ms ease, color 180ms ease;
}

.accordion[open] > .accordion__summary .accordion__chevron {
  transform: rotate(180deg);
  color: var(--blue);
}

.accordion__body {
  padding: 4px 18px 16px;
  color: var(--ink);
  font-size: 0.92rem;
  line-height: 1.55;
  border-top: 1px solid var(--line);
}

.accordion__body > :first-child {
  margin-top: 10px;
}
.accordion__body > :last-child {
  margin-bottom: 0;
}
</style>
