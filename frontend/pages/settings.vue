<script setup lang="ts">
const { preference, setPreference } = useAppTheme()

onMounted(() => {
  if (import.meta.client) {
    const raw = localStorage.getItem("ryw_theme")
    if (raw === "light" || raw === "dark" || raw === "system") preference.value = raw
  }
})
</script>

<template>
  <div id="main-content" class="settings-page" tabindex="-1">
    <PageHero
      eyebrow="Settings"
      subtitle="Session · appearance"
      title="Settings"
      description="Appearance and session notes. Theme is stored in this browser only; it applies across Home, Dashboard, Market, and Audit."
    />

    <section class="card" aria-labelledby="appearance-heading">
      <h2 id="appearance-heading">Appearance</h2>
      <fieldset class="theme-fieldset">
        <legend class="sr-only">Color theme</legend>
        <label class="radio-row">
          <input type="radio" name="theme" value="light" :checked="preference === 'light'" @change="setPreference('light')" />
          Light
        </label>
        <label class="radio-row">
          <input type="radio" name="theme" value="dark" :checked="preference === 'dark'" @change="setPreference('dark')" />
          Dark
        </label>
        <label class="radio-row">
          <input
            type="radio"
            name="theme"
            value="system"
            :checked="preference === 'system'"
            @change="setPreference('system')"
          />
          Match system
        </label>
      </fieldset>
      <p class="hint">Theme applies across Home, Dashboard, Market, and Audit. Preference is stored in this browser.</p>
    </section>
  </div>
</template>

<style scoped>
.settings-page {
  max-width: 40rem;
  margin: 0 auto;
  padding: 1.5rem 1rem 3rem;
}
.page-head {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1.5rem;
}
.page-head h1 {
  margin: 0 0 0.35rem;
  font-size: 1.5rem;
}
.muted {
  margin: 0;
  color: var(--muted);
  font-size: 0.9rem;
}
.nav-links {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  align-items: flex-start;
}
.link-btn {
  padding: 0.4rem 0.75rem;
  border: 1px solid var(--line-strong);
  border-radius: 6px;
  font-size: 0.9rem;
  background: var(--surface-2);
  color: var(--ink);
}
.card {
  padding: 1.25rem;
  border: 1px solid var(--line);
  border-radius: 10px;
  background: var(--surface);
  margin-bottom: 1rem;
}
.card h2 {
  margin: 0 0 1rem;
  font-size: 1.1rem;
}
.theme-fieldset {
  border: none;
  padding: 0;
  margin: 0 0 0.75rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.radio-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  font-size: 0.95rem;
}
.hint {
  margin: 0;
  font-size: 0.85rem;
  color: var(--muted);
}
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}
</style>
