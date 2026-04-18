# Ride YourWay x PJTL - Documentation Index

This directory is the single source of truth for how the Ride YourWay market
viability dashboard is built, deployed, and operated. Every document explains
both the **what** (mechanics) and the **why** (design intent), and cites the
exact files that implement the behavior.

The documentation is organized by concern so that newcomers can read it in the
order most relevant to their role.

## Reading order by role

### New engineer (onboarding in an afternoon)
1. [architecture/system-overview.md](architecture/system-overview.md)
2. [ops/running-locally.md](ops/running-locally.md)
3. [architecture/folder-contract.md](architecture/folder-contract.md)
4. [data-pipeline/overview.md](data-pipeline/overview.md)
5. [api/rest-endpoints.md](api/rest-endpoints.md)
6. [frontend/spa-navigation.md](frontend/spa-navigation.md)

### Data / ML engineer
1. [data-pipeline/overview.md](data-pipeline/overview.md)
2. [data-pipeline/phase1-extract.md](data-pipeline/phase1-extract.md)
3. [data-pipeline/training-rows.md](data-pipeline/training-rows.md)
4. [data-pipeline/training-base.md](data-pipeline/training-base.md)
5. [ml/training.md](ml/training.md)
6. [ml/sensitivity-harness.md](ml/sensitivity-harness.md)
7. [ml/model-card.md](ml/model-card.md)

### Frontend engineer
1. [frontend/spa-navigation.md](frontend/spa-navigation.md)
2. [frontend/component-catalog.md](frontend/component-catalog.md)
3. [frontend/theming.md](frontend/theming.md)
4. [frontend/upload-ux.md](frontend/upload-ux.md)

### Ops / platform
1. [ops/docker.md](ops/docker.md)
2. [ops/environment-variables.md](ops/environment-variables.md)
3. [ops/security-todos.md](ops/security-todos.md)
4. [production-checklist.md](production-checklist.md)

### Product / analyst
1. [kpi/gate-logic.md](kpi/gate-logic.md)
2. [kpi/tier-policy.md](kpi/tier-policy.md)
3. [kpi/assumption-register.md](kpi/assumption-register.md)
4. [glossary.md](glossary.md)

## Full index

### Architecture
- [architecture/system-overview.md](architecture/system-overview.md) - monorepo
  components, deploy topology, request flow.
- [architecture/folder-contract.md](architecture/folder-contract.md) - the
  `code/inputs/`, `code/intermediates/`, `code/outputs/` contract.
- [architecture/spa-layout.md](architecture/spa-layout.md) - `layouts/default.vue`,
  shared state, component tree.
- [architecture/hld.md](architecture/hld.md) - expanded high-level design.
- [architecture/lld.md](architecture/lld.md) - module-by-module low-level design.

### Data pipeline
- [data-pipeline/overview.md](data-pipeline/overview.md) - end-to-end mermaid
  and the canonical run order.
- [data-pipeline/phase1-extract.md](data-pipeline/phase1-extract.md) - phase-1
  canonical base build.
- [data-pipeline/training-rows.md](data-pipeline/training-rows.md) - bulk,
  boundary, and flip populations for training rows.
- [data-pipeline/training-base.md](data-pipeline/training-base.md) - gate-rule
  labeling that produces `label_ready`.
- [data-pipeline/sync-and-manifests.md](data-pipeline/sync-and-manifests.md) -
  the inference-inputs snapshot and its manifests.

### Source workbooks
- [workbooks/sheet-inventory.md](workbooks/sheet-inventory.md) - every sheet
  in `code/inputs/*.xlsx` and the meeting Gantt, mapped back to the nine
  gates, the seven design-doc modules, and the CEO's six student
  deliverables.
- [workbooks/operational-eda.md](workbooks/operational-eda.md) - narrative
  report for the 10-section operational EDA (fleetwise scorecard, weekly
  trend, mode mix, OTP, payer concentration, hourly demand, cancellations,
  rev/Kent-Leg, SecureCare vs fleet, regional cost estimate). Every number
  is cited back to a CSV in `code/outputs/reports/operational_eda/`.
- [deliverables.md](deliverables.md) - catalog of the six in-scope
  deliverables, the ten new value-add deliverables (D1..D10), and the
  items deferred until RYW ships additional data.

### ML
- [ml/training.md](ml/training.md) - XGBoost training, calibration, export.
- [ml/sensitivity-harness.md](ml/sensitivity-harness.md) - T1..T6 contract.
- [ml/model-card.md](ml/model-card.md) - intended use, metrics, lineage.
- [ml/feature-reference.md](ml/feature-reference.md) - nine features,
  thresholds, pass rules.

### API
- [api/rest-endpoints.md](api/rest-endpoints.md) - every route.
- [api/upload-workflow.md](api/upload-workflow.md) - job lifecycle.
- [api/roles-and-auth.md](api/roles-and-auth.md) - header vs JWT mode.

### Ops
- [ops/docker.md](ops/docker.md) - compose, `RYW_REPO_ROOT`, `/workspace`.
- [ops/environment-variables.md](ops/environment-variables.md) - `RYW_*` and
  `NUXT_*`.
- [ops/running-locally.md](ops/running-locally.md) - venv, deps, notebooks.
- [ops/security-todos.md](ops/security-todos.md) - JWT, CORS, secret, errors.

### Frontend
- [frontend/component-catalog.md](frontend/component-catalog.md) - every Vue
  component.
- [frontend/theming.md](frontend/theming.md) - design tokens and overrides.
- [frontend/spa-navigation.md](frontend/spa-navigation.md) - the SPA shell.
- [frontend/upload-ux.md](frontend/upload-ux.md) - intake UX and guard rails.

### KPI and analytics
- [kpi/gate-logic.md](kpi/gate-logic.md) - nine gates, thresholds, pass rules.
- [kpi/assumption-register.md](kpi/assumption-register.md) - v2 planning
  formula, Kent-Leg, cost ceiling.
- [kpi/tier-policy.md](kpi/tier-policy.md) - Tier 1 / 2 / 3 definitions.

### Testing
- [testing/test-strategy.md](testing/test-strategy.md) - pytest, harness,
  smokes.

### Decisions
- [decision-records/0001-spa-architecture.md](decision-records/0001-spa-architecture.md)
- [decision-records/0002-model-artifact-location.md](decision-records/0002-model-artifact-location.md)
- [decision-records/0003-code-folder-reorg.md](decision-records/0003-code-folder-reorg.md)
- [decision-records/0004-maize-blue-branding.md](decision-records/0004-maize-blue-branding.md)

### Reference
- [glossary.md](glossary.md) - Kent-Leg, SecureCare, readiness gate, tier,
  provisional, and other domain terms.
- [changelog.md](changelog.md) - chronological ledger of every dated commit in
  `main`.
- [production-checklist.md](production-checklist.md) - pre-deploy gate list.

## Conventions

- File paths are written relative to the git repo root (the `code/`
  directory that holds this docs folder). We link to them with
  repo-relative links such as
  [code/config/pjtl_kpis_and_formulas.json](../config/pjtl_kpis_and_formulas.json).
- Backticks are used for identifiers, env vars, and HTTP verbs.
- Mermaid diagrams are embedded in overview-level docs.
- Every doc includes a **Why** section when the design is non-obvious.
