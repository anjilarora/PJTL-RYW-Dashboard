<script setup lang="ts">
defineProps<{
  title: string
  items: Array<{
    label: string
    value: number
    display: string
  }>
  color?: string
}>()
</script>

<template>
  <div class="panel">
    <div class="panel-header">
      <h3>{{ title }}</h3>
    </div>
    <div class="bar-list">
      <div
        v-for="item in items"
        :key="item.label"
        class="bar-row"
      >
        <div class="bar-row-top">
          <span>{{ item.label }}</span>
          <strong>{{ item.display }}</strong>
        </div>
        <div class="bar-track">
          <div
            class="bar-fill"
            :style="{
              width: `${(item.value / Math.max(...items.map((entry) => entry.value))) * 100}%`,
              background: color || 'linear-gradient(90deg, #14b8a6, #2563eb)'
            }"
          />
        </div>
      </div>
    </div>
  </div>
</template>
