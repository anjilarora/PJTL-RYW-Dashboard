<script setup lang="ts">
/**
 * Default SPA shell: every route renders inside the same topbar +
 * main-shell container so the dashboard, home, market, audit, and settings
 * pages all share one nav and one layout rhythm. The role dropdown in the
 * nav is bound to the shared useBackendApi role so switching roles on any
 * page applies everywhere without a reload.
 */
const { role } = useBackendApi()
</script>

<template>
  <div class="app-shell">
    <a class="skip-link" href="#main-content">Skip to main content</a>
    <main class="app-shell__main dashboard-app">
      <section class="main-shell">
        <DashboardTopbar v-model="role" />
        <slot />
      </section>
    </main>
  </div>
</template>

<style scoped>
.skip-link {
  position: absolute;
  left: -9999px;
  z-index: 999;
  padding: 0.5rem 1rem;
  background: var(--blue);
  color: var(--white);
  text-decoration: none;
  border-radius: 6px;
}
.skip-link:focus {
  left: 0.5rem;
  top: 0.5rem;
}
</style>
