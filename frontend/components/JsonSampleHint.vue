<script setup lang="ts">
/**
 * Collapsible "Show sample JSON" helper. Renders a pretty-printed example and
 * an "Insert example" button so users do not have to guess the schema when
 * pasting into a JSON textarea.
 */
const props = defineProps<{
  title?: string
  sample: unknown
  description?: string
}>()
const emit = defineEmits<{ (e: "insert", value: string): void }>()

const pretty = computed(() => JSON.stringify(props.sample, null, 2))
const copied = ref(false)

function insert() {
  emit("insert", pretty.value)
}

async function copyToClipboard() {
  try {
    await navigator.clipboard.writeText(pretty.value)
    copied.value = true
    setTimeout(() => (copied.value = false), 1500)
  } catch {
    /* ignore */
  }
}
</script>

<template>
  <details class="json-sample">
    <summary class="json-sample__summary">
      <svg viewBox="0 0 24 24" width="14" height="14" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="9" />
        <path d="M12 8h.01" />
        <path d="M11 12h1v4h1" />
      </svg>
      <span>{{ title || "Show sample JSON" }}</span>
    </summary>
    <div class="json-sample__body">
      <p v-if="description" class="json-sample__desc">{{ description }}</p>
      <pre class="json-sample__code"><code>{{ pretty }}</code></pre>
      <div class="json-sample__actions">
        <button type="button" class="json-sample__btn" @click="insert">Insert example</button>
        <button type="button" class="json-sample__btn json-sample__btn--ghost" @click="copyToClipboard">
          {{ copied ? "Copied" : "Copy" }}
        </button>
      </div>
    </div>
  </details>
</template>

<style scoped>
.json-sample {
  margin: 6px 0 10px;
  border: 1px solid var(--line);
  border-radius: 10px;
  background: var(--surface-2);
  overflow: hidden;
}
.json-sample__summary {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  width: 100%;
  padding: 8px 12px;
  cursor: pointer;
  user-select: none;
  color: var(--muted);
  font-size: 0.85rem;
  font-weight: 600;
}
.json-sample__summary:hover { color: var(--blue); }
.json-sample__summary::-webkit-details-marker { display: none; }
.json-sample[open] .json-sample__summary { color: var(--blue); }

.json-sample__body {
  padding: 10px 12px 12px;
  border-top: 1px solid var(--line);
  background: var(--surface);
}
.json-sample__desc {
  margin: 0 0 8px;
  color: var(--muted);
  font-size: 0.85rem;
}
.json-sample__code {
  margin: 0 0 8px;
  padding: 10px 12px;
  background: var(--surface-3, var(--surface-2));
  border: 1px solid var(--line);
  border-radius: 8px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 0.78rem;
  line-height: 1.55;
  color: var(--ink);
  white-space: pre;
  overflow-x: auto;
  max-height: 260px;
}
.json-sample__actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.json-sample__btn {
  appearance: none;
  border: 1px solid var(--line-strong);
  border-radius: 999px;
  padding: 5px 12px;
  font-size: 0.8rem;
  font-weight: 700;
  background: var(--blue);
  color: var(--white);
  cursor: pointer;
}
.json-sample__btn:hover { filter: brightness(1.08); }
.json-sample__btn--ghost {
  background: transparent;
  color: var(--ink);
}
.json-sample__btn--ghost:hover { background: var(--surface-2); }
</style>
