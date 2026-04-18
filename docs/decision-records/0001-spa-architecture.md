# ADR 0001 - Single-page application with a shared layout

## Status

Accepted (2026-04-15).

## Context

The frontend started as a set of Nuxt pages that each imported their own
copy of `DashboardTopbar`, `RywLogo`, and the theme toggle. Three
recurring problems appeared:

1. The role switcher lived in multiple places and could desync (one page
   had the user as `admin` while another still sent `X-Role: analyst`).
2. Small copy or logo changes required edits in four files.
3. Cross-route navigation remounted the chrome, producing visible
   flicker on slower devices.

## Decision

Consolidate all chrome into `code/frontend/layouts/default.vue` and
adopt a single-page application model where every route renders inside
that layout. Share state via composables (`useBackendApi`,
`useAppTheme`, `useViabilitySession`) so pages do not need to
re-synchronize.

Specifically:

- `layouts/default.vue` mounts `DashboardTopbar` once.
- `DashboardTopbar` writes the role into `useBackendApi().role`, which
  every page reads.
- `useViabilitySession` stashes the market profile and most recent
  evaluation in `sessionStorage` so navigation does not trigger a
  re-fetch.
- Tabs inside `pages/dashboard.vue` (including the "Gate detail" tab)
  switch via local state; they do not push a new route.

## Consequences

- Consistent chrome across `/`, `/market`, `/dashboard`, `/audit`,
  `/settings`.
- Page transitions are instant; only the body changes.
- `DashboardTopbar` must be defensive about the current route since it
  is always mounted.
- `useViabilitySession` keys (`RYW_STORAGE_MARKET`,
  `RYW_STORAGE_HISTORICAL`) are part of the app contract; renaming
  them is a user-visible session invalidation event.

## Alternatives considered

- **Keep per-page chrome.** Rejected due to the desync problem.
- **Multi-page app with a service worker caching state.** Overkill for
  the three-page core flow.
- **Nuxt nested routes with `<NuxtLayout>` per section.** The chrome
  is identical across every page, so nesting layouts would add
  complexity without payoff.
