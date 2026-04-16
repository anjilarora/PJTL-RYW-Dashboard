<script setup lang="ts">
const props = withDefaults(
  defineProps<{
    label: string
    value: number
    max: number
    formatted?: string
    thresholdLabel?: string
    tone?: "pass" | "fail" | "neutral" | "provisional" | "auto"
    threshold?: number
    thresholdComparator?: "gte" | "lte"
  }>(),
  { tone: "auto", thresholdComparator: "gte" }
)

const pct = computed(() => {
  if (!props.max) return 0
  return Math.max(0, Math.min(1, props.value / props.max)) * 100
})
const resolvedTone = computed(() => {
  if (props.tone !== "auto") return props.tone
  if (typeof props.threshold !== "number") return "neutral"
  if (props.thresholdComparator === "lte") {
    return props.value <= props.threshold ? "pass" : "fail"
  }
  return props.value >= props.threshold ? "pass" : "fail"
})
</script>

<template>
  <div class="bar-stat" :class="`bar-stat--${resolvedTone}`">
    <div class="bar-stat__head">
      <span class="bar-stat__label">{{ label }}</span>
      <strong class="bar-stat__value">{{ formatted ?? value }}</strong>
    </div>
    <div class="bar-stat__track" role="progressbar" :aria-valuenow="value" :aria-valuemax="max" :aria-valuemin="0" :aria-label="label">
      <div class="bar-stat__fill" :style="{ width: `${pct}%` }" />
    </div>
    <div v-if="thresholdLabel" class="bar-stat__threshold">{{ thresholdLabel }}</div>
  </div>
</template>

<style scoped>
.bar-stat {
  display: grid;
  gap: 6px;
  padding: 14px;
  border-radius: 18px;
  background: var(--surface-2);
  border: 1px solid var(--line);
  min-width: 0;
}
.bar-stat__head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 10px;
}
.bar-stat__label {
  font-size: 0.82rem;
  color: var(--muted);
  line-height: 1.3;
}
.bar-stat__value {
  font-size: 1.05rem;
  font-weight: 700;
  color: var(--ink);
  letter-spacing: -0.02em;
  white-space: nowrap;
}
.bar-stat__track {
  height: 8px;
  border-radius: 999px;
  background: var(--line);
  overflow: hidden;
  opacity: 0.85;
}
.bar-stat__fill {
  height: 100%;
  border-radius: inherit;
  transition: width 360ms ease;
}
.bar-stat--pass .bar-stat__fill {
  background: linear-gradient(90deg, var(--teal), color-mix(in srgb, var(--teal) 60%, var(--maize)));
}
.bar-stat--fail .bar-stat__fill {
  background: linear-gradient(90deg, var(--red), color-mix(in srgb, var(--red) 70%, var(--amber)));
}
.bar-stat--provisional .bar-stat__fill {
  background: linear-gradient(90deg, var(--amber), var(--maize));
}
.bar-stat--neutral .bar-stat__fill {
  background: linear-gradient(90deg, var(--blue), var(--maize));
}
.bar-stat__threshold {
  font-size: 0.76rem;
  color: var(--muted-2);
}
</style>
