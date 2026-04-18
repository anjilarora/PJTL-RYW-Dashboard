# Changelog

A chronological ledger of the commits on `main`. Timestamps are America/New_York
(EDT, UTC-4), matching `GIT_AUTHOR_DATE` on each commit. Entries are authored
when the commit is pushed and should be appended-only.

## 2026-04-18 01:08:53 EDT - Documentation commit
Added the comprehensive `code/docs/` tree covering architecture, data pipeline,
ML, API, ops, frontend, KPIs, testing, decision records, glossary, and this
changelog. No code changes.

## 2026-04-15 21:24:17 EDT - xlsx-only upload + folders under code/
- Upload UI copy rewritten to read "Excel workbook (.xlsx) only" with the new
  InfoTip listing the canonical paths.
- Physically relocated `inputs/`, `intermediates/`, `outputs/` under `code/`.
- Added `code_root_from_anchor()` helper in
  [code/lib/repo_paths.py](../lib/repo_paths.py).
- Retargeted every script, notebook, Dockerfile `COPY`, and UI path string.
- Fixed stage-3 notebook regressions so `model_card.interpretation_artifact`
  and `metadata.training_data.path` stay repo-relative on every re-run.
- Regenerated all pipeline artifacts (phase-1 CSVs, training rows, inference
  inputs snapshot, model, stage reports/plots).

## 2026-04-15 21:02:41 EDT - Michigan maize-blue SPA
- Introduced [code/frontend/components/RywLogo.vue](../frontend/components/RywLogo.vue),
  [code/frontend/components/PageHero.vue](../frontend/components/PageHero.vue),
  [code/frontend/components/MarketHero.vue](../frontend/components/MarketHero.vue).
- Promoted `DashboardTopbar` to the global
  [code/frontend/layouts/default.vue](../frontend/layouts/default.vue).
- Converted every page to a shared SPA shell with client-side navigation and
  a shared `role` via `useBackendApi()`.
- Added
  [code/frontend/components/RingStat.vue](../frontend/components/RingStat.vue)
  and [code/frontend/components/BarStat.vue](../frontend/components/BarStat.vue)
  microcharts.
- Rebuilt `KpiSnapshotPanel.vue` with week tag and `InfoTip`.
- Turned `GateScorecard.vue` into a carousel; split the detail view into
  `GateDetailPanel.vue` (its own tab).
- Deleted `GateTable.vue`, `AssumptionRegisterPanel.vue`, `ConfidenceLegendPanel.vue`
  and the "Operations demo" tab.
- Rewrote `StatusPill.vue` with SVG icons, tone backgrounds, and the
  `--amber-ink` token; removed index labels ("1/9").

## 2026-04-11 18:14:56 EDT - Dashboard UX polish
- Redesigned `IntakeSummaryPanel.vue` with a plain-English takeaway and class
  breakdown.
- Rebuilt `MarginWaterfallPanel.vue` as tiles + bars.
- Introduced `CollapsibleCard.vue`.
- Converted `RiskMitigationPanel.vue`, `AuditTraceabilityPanel.vue`, and
  `SensitivityScenarioPanel.vue` to accordion containers.
- Polished `InfoTip.vue`; moved tier policy behind a circled-i.
- Deleted `AssumptionRegisterPanel.vue` (content moved into info tips to
  eliminate duplicate data).

## 2026-04-10 17:22:09 EDT - Light-mode CSS, upload fix, path scrub
- Added the dedicated light-mode override block in
  [code/frontend/assets/css/main.css](../frontend/assets/css/main.css) without
  disturbing dark-mode tokens.
- Repaired the upload pipeline session-storage bug in
  `code/frontend/pages/market.vue` (referenced undefined keys).
- Scrubbed internal repo path leaks from dashboard copy.
- Clarified "previous Q1 vs current file" ambiguity in data-source blurbs.
- Confirmed the Q1 workbook year is 2026.

## 2026-04-10 15:07:21 EDT - Model retrain + sensitivity harness
- Rebuilt
  [code/scripts/generate_readiness_training_rows.py](../scripts/generate_readiness_training_rows.py)
  with bulk, boundary, and flip populations.
- Updated
  [code/scripts/build_readiness_training_base.py](../scripts/build_readiness_training_base.py)
  to label rows via the gate rules in
  [code/config/pjtl_kpis_and_formulas.json](../config/pjtl_kpis_and_formulas.json).
- Tuned hyperparameters in
  [code/inference_engine/scripts/train_readiness_model_from_inputs.py](../inference_engine/scripts/train_readiness_model_from_inputs.py).
- Added
  [code/inference_engine/scripts/test_readiness_edge_cases.py](../inference_engine/scripts/test_readiness_edge_cases.py)
  enforcing the T1..T6 sensitivity contract.
- Exported model + metadata; the "1% flip" requirement is now verifiable.

## 2026-04-10 10:17:48 EDT - Symbol rendering polish
Replaced `gte` / `lte` / `lt` strings with the `>=` / `<=` / `<` glyphs across
gate and KPI surfaces in the UI.

## 2026-04-10 10:11:33 EDT - Connectivity + theme + KPI wiring
- Fixed Docker/compose wiring (including `NUXT_BACKEND_BASE_URL`).
- Added `server/api/backend/[...path].ts` proxy.
- Harmonized dark theme via CSS variables.
- Wired KPI definitions through `engine/kpi_config.load_kpi_document()` so
  `KpiSnapshotPanel` and the `/api/v1/kpis` route read the same JSON.
- Production-security TODOs moved out of `settings.vue` into
  [code/docs/production-checklist.md](production-checklist.md).

## 2026-04-09 20:04:12 EDT - Scaffold PJTL x Ride YourWay launch readiness monorepo
Initial scaffold: FastAPI backend (`code/backend/`), Nuxt frontend
(`code/frontend/`), inference engine (`code/inference_engine/`), KPI config,
intake workbooks, Dockerfiles, and baseline READMEs.
