<script setup lang="ts">
/**
 * Compact hero used by the secondary pages (Home, Market, Audit, Settings)
 * so every page on the dashboard gets the same maize/blue header rhythm
 * without the heavy readiness ring. For the dashboard itself use the
 * richer MarketHero component.
 */
defineProps<{
  eyebrow?: string
  title: string
  subtitle?: string
  description?: string
}>()
</script>

<template>
  <section class="page-hero" aria-label="Page header">
    <div class="page-hero__left">
      <div v-if="eyebrow || subtitle" class="page-hero__eyebrow">
        <span v-if="eyebrow" class="page-hero__pill">{{ eyebrow }}</span>
        <span v-if="subtitle" class="page-hero__subtitle">{{ subtitle }}</span>
      </div>
      <h1 class="page-hero__title">{{ title }}</h1>
      <p v-if="description" class="page-hero__desc">{{ description }}</p>
      <div v-if="$slots.chips" class="page-hero__chips">
        <slot name="chips" />
      </div>
    </div>
    <div v-if="$slots.actions" class="page-hero__actions">
      <slot name="actions" />
    </div>
  </section>
</template>

<style scoped>
.page-hero {
  position: relative;
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 16px;
  padding: 22px 26px;
  margin-top: 14px;
  border-radius: 24px;
  border: 1px solid var(--line);
  background:
    radial-gradient(circle at 0% 0%, var(--maize-soft), transparent 60%),
    radial-gradient(circle at 100% 0%, var(--blue-soft), transparent 55%),
    var(--surface);
  box-shadow: var(--shadow);
  overflow: hidden;
}
.page-hero::before {
  content: "";
  position: absolute;
  inset: auto 0 0 0;
  height: 3px;
  background: linear-gradient(90deg, var(--blue), var(--maize));
  opacity: 0.85;
}
.page-hero__left {
  min-width: 0;
}
.page-hero__eyebrow {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
  margin-bottom: 8px;
}
.page-hero__pill {
  display: inline-flex;
  padding: 5px 10px;
  border-radius: 999px;
  background: var(--maize-soft);
  color: var(--maize-ink);
  border: 1px solid color-mix(in srgb, var(--maize) 40%, transparent);
  font-size: 0.7rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}
.page-hero__subtitle {
  font-size: 0.86rem;
  color: var(--muted);
  font-weight: 600;
}
.page-hero__title {
  margin: 0;
  font-size: clamp(1.4rem, 2.2vw, 1.9rem);
  letter-spacing: -0.03em;
  line-height: 1.15;
  color: var(--ink);
}
.page-hero__desc {
  margin: 8px 0 0;
  color: var(--muted);
  line-height: 1.55;
  font-size: 0.95rem;
}
.page-hero__chips {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 12px;
}
.page-hero__actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: flex-end;
  justify-content: center;
}
@media (max-width: 780px) {
  .page-hero {
    grid-template-columns: 1fr;
  }
  .page-hero__actions {
    align-items: flex-start;
  }
}
</style>
