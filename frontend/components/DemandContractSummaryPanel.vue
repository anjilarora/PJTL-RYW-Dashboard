<script setup lang="ts">
defineProps<{
  prospective: { completedTripsPerWeek: number; qualitySharePct: number; topProgramVolumeSharePct: number }
}>()
</script>

<template>
  <article class="panel">
    <div class="panel-eyebrow">Demand and Contracts</div>
    <h2>Demand and Concentration</h2>
    <div class="baseline-grid">
      <div class="baseline-stat">
        <span>Completed trips / week</span>
        <strong>{{ prospective.completedTripsPerWeek }}</strong>
      </div>
      <div class="baseline-stat">
        <span>Quality share</span>
        <strong>{{ prospective.qualitySharePct.toFixed(1) }}%</strong>
      </div>
      <div class="baseline-stat">
        <span>Top program concentration</span>
        <strong>{{ prospective.topProgramVolumeSharePct.toFixed(1) }}%</strong>
      </div>
    </div>
  </article>
</template>
