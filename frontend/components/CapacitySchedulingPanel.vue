<script setup lang="ts">
defineProps<{
  readiness: { projectedRoadHoursPerVehicleDay: number; projectedHigherAcuitySharePct: number }
}>()
</script>

<template>
  <article class="panel">
    <div class="panel-eyebrow">Capacity and Scheduling</div>
    <h2>Fleet Intensity</h2>
    <div class="baseline-grid">
      <div class="baseline-stat">
        <span>Road hrs / vehicle / day</span>
        <strong>{{ readiness.projectedRoadHoursPerVehicleDay.toFixed(2) }}</strong>
      </div>
      <div class="baseline-stat">
        <span>Higher-acuity share</span>
        <strong>{{ readiness.projectedHigherAcuitySharePct.toFixed(1) }}%</strong>
      </div>
    </div>
  </article>
</template>
