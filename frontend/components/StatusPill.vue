<script setup lang="ts">
/**
 * Colored, icon-prefixed status chip used by gate cards, the gate detail
 * pane, and anywhere we want to show pass / fail / provisional outcomes.
 * Backgrounds and borders come from shared color tokens so pills stay
 * consistent in light and dark themes.
 */
type Tone = "pass" | "fail" | "provisional" | "neutral"

withDefaults(
  defineProps<{
    label: string
    tone?: Tone
    size?: "sm" | "md"
  }>(),
  { tone: "neutral", size: "md" }
)
</script>

<template>
  <span
    class="status-pill"
    :class="[`status-pill--${tone}`, `status-pill--${size}`]"
    :title="label"
  >
    <svg
      v-if="tone === 'pass'"
      class="status-pill__icon"
      viewBox="0 0 24 24"
      aria-hidden="true"
      fill="none"
      stroke="currentColor"
      stroke-width="2.6"
      stroke-linecap="round"
      stroke-linejoin="round"
    >
      <path d="M5 12l5 5 9-11" />
    </svg>
    <svg
      v-else-if="tone === 'fail'"
      class="status-pill__icon"
      viewBox="0 0 24 24"
      aria-hidden="true"
      fill="none"
      stroke="currentColor"
      stroke-width="2.6"
      stroke-linecap="round"
      stroke-linejoin="round"
    >
      <path d="M6 6l12 12" />
      <path d="M18 6L6 18" />
    </svg>
    <svg
      v-else-if="tone === 'provisional'"
      class="status-pill__icon"
      viewBox="0 0 24 24"
      aria-hidden="true"
      fill="none"
      stroke="currentColor"
      stroke-width="2.4"
      stroke-linecap="round"
      stroke-linejoin="round"
    >
      <circle cx="12" cy="12" r="9" />
      <path d="M12 7v6" />
      <circle cx="12" cy="16.5" r="0.6" fill="currentColor" stroke="none" />
    </svg>
    <svg
      v-else
      class="status-pill__icon"
      viewBox="0 0 24 24"
      aria-hidden="true"
      fill="none"
      stroke="currentColor"
      stroke-width="2.4"
      stroke-linecap="round"
      stroke-linejoin="round"
    >
      <circle cx="12" cy="12" r="9" />
    </svg>
    <span class="status-pill__label">{{ label }}</span>
  </span>
</template>

<style scoped>
.status-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px 4px 8px;
  border-radius: 999px;
  font-weight: 800;
  font-size: 0.78rem;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  border: 1px solid transparent;
  line-height: 1;
  white-space: nowrap;
  font-variant-numeric: tabular-nums;
}
.status-pill--sm {
  padding: 3px 8px 3px 6px;
  font-size: 0.7rem;
  gap: 4px;
}
.status-pill__icon {
  width: 14px;
  height: 14px;
  flex-shrink: 0;
}
.status-pill--sm .status-pill__icon {
  width: 12px;
  height: 12px;
}

.status-pill--pass {
  background: var(--teal-soft);
  color: var(--teal);
  border-color: color-mix(in srgb, var(--teal) 45%, transparent);
}
.status-pill--fail {
  background: var(--red-soft);
  color: var(--red);
  border-color: color-mix(in srgb, var(--red) 45%, transparent);
}
.status-pill--provisional {
  background: var(--amber-soft);
  color: var(--amber-ink, var(--amber));
  border-color: color-mix(in srgb, var(--amber) 55%, transparent);
}
.status-pill--neutral {
  background: var(--surface-2);
  color: var(--muted);
  border-color: var(--line);
}
</style>
