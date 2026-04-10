<script setup lang="ts">
defineProps<{
  readiness: { projectedWeeklyRevenue: number; projectedMarginPct: number; projectedRevenuePerKentLeg: number }
  prospective: { projectedCost: number }
}>()
</script>

<template>
  <article class="panel">
    <div class="panel-eyebrow">Cost and Revenue</div>
    <h2>Economics Summary</h2>
    <div class="baseline-grid">
      <div class="baseline-stat">
        <span>Projected weekly revenue</span>
        <strong>${{ readiness.projectedWeeklyRevenue.toFixed(0) }}</strong>
      </div>
      <div class="baseline-stat">
        <span>Projected weekly cost</span>
        <strong>${{ prospective.projectedCost.toFixed(0) }}</strong>
      </div>
      <div class="baseline-stat">
        <span>Revenue / Kent-Leg</span>
        <strong>${{ readiness.projectedRevenuePerKentLeg.toFixed(2) }}</strong>
      </div>
      <div class="baseline-stat">
        <span>Projected margin</span>
        <strong>{{ readiness.projectedMarginPct.toFixed(1) }}%</strong>
      </div>
    </div>
  </article>
</template>
