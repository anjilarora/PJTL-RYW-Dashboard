<script setup lang="ts">
import logoUrl from "~/assets/logo/ryw-logo.png"

withDefaults(
  defineProps<{
    height?: number
    alt?: string
    padded?: boolean
  }>(),
  { height: 28, alt: "Ride YourWay", padded: true }
)
</script>

<template>
  <span class="ryw-logo-wrap" :class="{ 'ryw-logo-wrap--padded': padded }">
    <img
      :src="logoUrl"
      :alt="alt"
      class="ryw-logo"
      :style="{ height: `${height}px` }"
      draggable="false"
    />
  </span>
</template>

<style scoped>
.ryw-logo-wrap {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  line-height: 0;
  user-select: none;
}
.ryw-logo {
  display: block;
  width: auto;
  object-fit: contain;
}
/* The bundled RYW mark uses black text for "YourWay" plus the road glyph.
   On dark surfaces we sit it on a tiny white plaque so brand colors stay
   intact instead of inverting them. Light mode needs no plaque. */
.ryw-logo-wrap--padded {
  padding: 4px 10px;
  border-radius: 10px;
  background: #ffffff;
  box-shadow: 0 1px 0 rgba(15, 23, 42, 0.04);
}
html[data-theme="light"] .ryw-logo-wrap--padded {
  background: transparent;
  padding: 0;
  box-shadow: none;
}
</style>
