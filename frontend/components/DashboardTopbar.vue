<script setup lang="ts">
/**
 * Global top navigation. Role selection was removed from the UI – every API
 * call is issued with the admin role (see `useBackendApi`) so no page is ever
 * blocked by permissions in this demo.
 */
</script>

<template>
  <header class="nav-bar" role="banner">
    <NuxtLink to="/" class="nav-brand" aria-label="Ride YourWay home">
      <RywLogo :height="32" />
      <span class="nav-brand__text">
        <span class="nav-brand__title">Market Viability Dashboard</span>
      </span>
    </NuxtLink>

    <nav class="nav-links" aria-label="Primary">
      <NuxtLink to="/" class="nav-link" active-class="nav-link--active" exact-active-class="nav-link--active">
        <svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
          <path d="M3 10.5 12 3l9 7.5" />
          <path d="M5 9v11h14V9" />
        </svg>
        <span>Home</span>
      </NuxtLink>

      <NuxtLink to="/dashboard" class="nav-link" active-class="nav-link--active">
        <svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
          <rect x="3" y="3" width="8" height="8" rx="1.5" />
          <rect x="13" y="3" width="8" height="5" rx="1.5" />
          <rect x="13" y="10" width="8" height="11" rx="1.5" />
          <rect x="3" y="13" width="8" height="8" rx="1.5" />
        </svg>
        <span>Dashboard</span>
      </NuxtLink>

      <NuxtLink to="/margin" class="nav-link" active-class="nav-link--active">
        <svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
          <rect x="3" y="3" width="18" height="18" rx="3" />
          <path d="M8 16l8-8" />
          <circle cx="9" cy="9" r="1.3" />
          <circle cx="15" cy="15" r="1.3" />
        </svg>
        <span>Margin calculator</span>
      </NuxtLink>

      <div class="nav-link-wrap">
        <NuxtLink to="/market" class="nav-link" active-class="nav-link--active">
          <svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="9" />
            <path d="M3 12h18" />
            <path d="M12 3c3 3.5 3 14 0 18" />
            <path d="M12 3c-3 3.5-3 14 0 18" />
          </svg>
          <span>Market Readiness</span>
        </NuxtLink>
        <InfoTip
          label="What is Market Readiness?"
          content="Upload an intake workbook for a prospective market to get a Go / No-Go decision, a readiness score, and a gate-by-gate breakdown. The dashboard stays on the Q1 2026 reference view."
          placement="bottom"
        />
      </div>
    </nav>

    <div class="nav-actions">
      <NuxtLink to="/settings" class="nav-icon-btn" aria-label="Settings">
        <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="3.2" />
          <path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3h.1a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5h.1a1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8v.1a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z" />
        </svg>
      </NuxtLink>
    </div>
  </header>
</template>

<style scoped>
.nav-bar {
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  gap: 20px;
  padding: 12px 20px;
  border-radius: 20px;
  background: var(--surface);
  border: 1px solid var(--line);
  box-shadow: var(--shadow);
  position: sticky;
  top: 14px;
  z-index: 30;
  backdrop-filter: blur(10px);
}
.nav-brand {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  color: var(--ink);
  padding: 2px 4px 2px 2px;
  border-radius: 12px;
}
.nav-brand__text {
  display: grid;
  align-items: center;
  line-height: 1.15;
  border-left: 1px solid var(--line);
  padding-left: 12px;
}
.nav-brand__title {
  font-family: "IBM Plex Sans", "Segoe UI", Arial, sans-serif;
  font-size: 1rem;
  font-weight: 700;
  color: var(--ink);
  letter-spacing: -0.005em;
  white-space: nowrap;
}
.nav-links {
  display: inline-flex;
  justify-content: center;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
  min-width: 0;
}
.nav-link-wrap {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  padding: 2px 4px 2px 2px;
  border-radius: 12px;
}
.nav-link-wrap:has(.nav-link--active) {
  background: var(--blue-soft);
}
.nav-link {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 8px 12px;
  border-radius: 10px;
  color: var(--muted);
  font-size: 0.9rem;
  font-weight: 600;
  transition: color 150ms ease, background 150ms ease;
}
.nav-link:hover {
  background: var(--surface-2);
  color: var(--ink);
}
.nav-link--active {
  background: var(--blue-soft);
  color: var(--blue);
}
.nav-link--active::after {
  content: "";
  display: block;
  position: relative;
  margin-left: 2px;
  width: 6px;
  height: 6px;
  border-radius: 999px;
  background: var(--maize);
}
.nav-actions {
  display: inline-flex;
  align-items: center;
  gap: 10px;
}
.nav-icon-btn {
  display: inline-grid;
  place-items: center;
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: var(--surface-2);
  border: 1px solid var(--line);
  color: var(--ink);
  transition: background 150ms ease, color 150ms ease;
}
.nav-icon-btn:hover {
  background: var(--maize-soft);
  color: var(--maize-ink);
  border-color: color-mix(in srgb, var(--maize) 35%, var(--line));
}

@media (max-width: 1040px) {
  .nav-bar {
    grid-template-columns: 1fr auto;
    row-gap: 10px;
  }
  .nav-links {
    grid-column: 1 / -1;
    justify-content: flex-start;
  }
}
@media (max-width: 860px) {
  .nav-brand__text {
    display: none;
  }
}
@media (max-width: 640px) {
  .nav-link span {
    display: none;
  }
  .nav-link {
    padding: 8px;
  }
}
</style>
