# SPA navigation

Ride YourWay's frontend is a single-page application: one layout, five
routes, shared state via composables, and client-side navigation via
Nuxt's `<NuxtLink>`.

## Routes

| Path | File | Purpose |
|---|---|---|
| `/` | `pages/index.vue` | Landing page. Hero + sensitivity sliders + "Try a market" CTA. |
| `/market` | `pages/market.vue` | Intake entry and evaluation trigger. Pushes the result into `useViabilitySession()`. |
| `/dashboard` | `pages/dashboard.vue` | Main readiness dashboard with tabbed panels. |
| `/audit` | `pages/audit.vue` | Audit trail + traceability view. |
| `/settings` | `pages/settings.vue` | UI preferences (theme only). |

All five mount inside `layouts/default.vue`.

## Shared state

Two composables do the heavy lifting:

### `useBackendApi()`

- `apiGet(path)`, `apiPost(path, body)`, `apiUpload(path, formData)` -
  attach request headers expected by the backend runtime and return parsed
  JSON.
- 502s from the Nitro proxy get normalized to `Error` with
  `statusCode === 502` so the UI can render "API unreachable".

### `useViabilitySession()`

- Stashes the current market profile under `RYW_STORAGE_MARKET`.
- Stashes the most recent evaluation under `RYW_STORAGE_HISTORICAL`.
- Exposes reactive refs so `/dashboard` reads the evaluation that
  `/market` just produced without an extra API call.

The previous bug where `/market` referenced `STORAGE_MARKET` and
`STORAGE_HISTORICAL` (undefined) was fixed by importing the canonical
keys from this composable.

## Page transitions

Nuxt default transitions are enabled. Because `layouts/default.vue`
hosts `DashboardTopbar`, navigating between pages does not remount the
topbar - only the page body fades. Theme preference continues to apply
across routes via shared state.

## Tab within a page

`pages/dashboard.vue` implements **tabs inside a single route** using
an internal `activeTab` ref. When a user clicks a gate card in
`GateScorecard.vue`, the card emits `@select(gateKey)`; the dashboard
switches `activeTab` to `"gate-detail"` and passes the key to
`GateDetailPanel.vue`. No route change, no refetch.

## Why SPA

Three reasons:

1. **Consistent chrome.** Global nav and shared context stay visually
   stable across routes, which avoids duplicate headers and keeps
   orientation clear.
2. **Fast transitions.** The readiness dashboard is numeric and
   scanner-heavy; users flip between `/dashboard` and `/audit` a lot.
3. **Shared evaluation state.** The viability session object is large
   (~40 KB JSON); transferring it between routes via `sessionStorage`
   beats re-running `/viability/evaluate`.

See [decision-records/0001-spa-architecture.md](../decision-records/0001-spa-architecture.md).

## Accessibility

- Every interactive element has a `role` and `aria-*` attributes where
  the native element does not already carry semantics (e.g., the
  custom tab strip on `dashboard.vue`).
- Tab order follows the DOM order inside the layout: topbar -> hero ->
  panels.
- `StatusPill` carries an `aria-label` equal to `status` so screen
  readers announce "Pass", "Provisional", or "Fail" regardless of the
  visual badge.
