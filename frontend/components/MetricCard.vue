<script setup lang="ts">
defineProps<{
  label: string
  value: string
  hint?: string
  tone?: "teal" | "navy" | "amber" | "red"
}>()
</script>

<template>
  <div class="metric-card" :class="tone ? `tone-${tone}` : 'tone-teal'">
    <div class="metric-label">{{ label }}</div>
    <div class="metric-value">{{ value }}</div>
    <div v-if="hint" class="metric-hint">{{ hint }}</div>
  </div>
</template>
