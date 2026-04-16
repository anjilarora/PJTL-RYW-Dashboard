<script setup lang="ts">
const props = withDefaults(
  defineProps<{
    label: string
    value: number
    max?: number
    suffix?: string
    threshold?: number
    thresholdLabel?: string
    tone?: "pass" | "fail" | "neutral" | "provisional" | "auto"
    size?: number
    strokeWidth?: number
    precision?: number
  }>(),
  {
    max: 100,
    suffix: "%",
    tone: "auto",
    size: 92,
    strokeWidth: 9,
    precision: 1
  }
)

const radius = computed(() => (props.size - props.strokeWidth) / 2)
const circumference = computed(() => 2 * Math.PI * radius.value)
const pct = computed(() => {
  if (!Number.isFinite(props.value) || !props.max) return 0
  return Math.max(0, Math.min(1, props.value / props.max))
})
const dash = computed(() => circumference.value * pct.value)
const resolvedTone = computed(() => {
  if (props.tone !== "auto") return props.tone
  if (typeof props.threshold !== "number") return "neutral"
  return props.value >= props.threshold ? "pass" : "fail"
})
const displayValue = computed(() => {
  if (!Number.isFinite(props.value)) return "—"
  return props.value.toFixed(props.precision)
})
</script>

<template>
  <div class="ring-stat" :class="`ring-stat--${resolvedTone}`">
    <div class="ring-stat__svg-wrap" :style="{ width: `${size}px`, height: `${size}px` }">
      <svg :width="size" :height="size" viewBox="0 0 100 100" class="ring-stat__svg" aria-hidden="true">
        <circle
          class="ring-stat__track"
          cx="50"
          cy="50"
          :r="(100 - strokeWidth * (100 / size)) / 2"
          :stroke-width="strokeWidth * (100 / size)"
          fill="none"
        />
        <circle
          class="ring-stat__fill"
          cx="50"
          cy="50"
          :r="(100 - strokeWidth * (100 / size)) / 2"
          :stroke-width="strokeWidth * (100 / size)"
          fill="none"
          :stroke-dasharray="`${dash * (100 / size)} ${circumference * (100 / size)}`"
          stroke-linecap="round"
          transform="rotate(-90 50 50)"
        />
      </svg>
      <div class="ring-stat__center">
        <strong>{{ displayValue }}<span>{{ suffix }}</span></strong>
      </div>
    </div>
    <div class="ring-stat__meta">
      <div class="ring-stat__label">{{ label }}</div>
      <div v-if="thresholdLabel" class="ring-stat__threshold">{{ thresholdLabel }}</div>
    </div>
  </div>
</template>

<style scoped>
.ring-stat {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px;
  border-radius: 18px;
  background: var(--surface-2);
  border: 1px solid var(--line);
}
.ring-stat__svg-wrap {
  position: relative;
  flex: 0 0 auto;
}
.ring-stat__svg {
  width: 100%;
  height: 100%;
}
.ring-stat__track {
  stroke: var(--line);
  opacity: 0.5;
}
.ring-stat__fill {
  transition: stroke-dasharray 360ms ease;
}
.ring-stat--pass .ring-stat__fill {
  stroke: var(--teal);
}
.ring-stat--fail .ring-stat__fill {
  stroke: var(--red);
}
.ring-stat--provisional .ring-stat__fill {
  stroke: var(--amber);
}
.ring-stat--neutral .ring-stat__fill {
  stroke: var(--blue);
}
.ring-stat__center {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  text-align: center;
}
.ring-stat__center strong {
  display: inline-flex;
  align-items: baseline;
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--ink);
  letter-spacing: -0.02em;
}
.ring-stat__center span {
  font-size: 0.7rem;
  font-weight: 600;
  color: var(--muted);
  margin-left: 2px;
}
.ring-stat__meta {
  min-width: 0;
}
.ring-stat__label {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--ink);
  line-height: 1.3;
}
.ring-stat__threshold {
  margin-top: 4px;
  font-size: 0.78rem;
  color: var(--muted-2);
}
</style>
