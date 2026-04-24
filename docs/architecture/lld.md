# Low-level design

Module-by-module walkthrough of the Ride YourWay backend, frontend, and
offline pipeline. The goal is that any engineer can open a file, read the
section here, and know what changes are safe to make.

## Backend

### `api/app.py`
Assembles the FastAPI application. Order of operations:

1. Configure logging to stdout at `RYW_LOG_LEVEL` (default `INFO`).
2. Warn if `RYW_ENV=production` is paired with `RYW_AUTH_MODE=header` or
   an empty `RYW_CORS_ORIGINS`.
3. Instantiate `FastAPI` with the structured description that explicitly
   calls out the demo auth mode.
4. Attach exception handler that returns `success=false` envelopes with a
   `request_id` and - in non-production or with `RYW_EXPOSE_INTERNAL_ERRORS=true` -
   the exception text.
5. Register middleware: `SlowAPIMiddleware`, `CORSMiddleware`,
   `RequestContextMiddleware`, optionally `InternalSecretMiddleware`.
6. Include every router; `operations_demo` only when
   `RYW_ENABLE_OPERATIONS_DEMO=true`.

### `api/config.py`
`pydantic-settings`-backed `Settings` class. Every field is keyed with the
`RYW_` env prefix. The `cors_origins_list` property falls back to
`http://localhost:3000`, `http://127.0.0.1:3000`, `http://frontend:3000`
when the env var is unset. A field validator converts an empty
`RYW_INTERNAL_API_SECRET` string into `None` so Docker Compose can pass
`${RYW_INTERNAL_API_SECRET:-}` without enabling enforcement.

### `api/auth.py`
Implements the `get_role` FastAPI dependency. When `RYW_AUTH_MODE=header`
it reads `X-Role`; when `jwt` it requires `Authorization: Bearer <token>`
and decodes it with `PyJWT`. `require_role(minimum, actual)` raises 403
when the caller's role is below the required rank. The rank map is
`analyst=1, ops=2, admin=3`.

### `api/repo_root.py`
Walks up from the application directory looking for `code/config/`. When
`RYW_REPO_ROOT` is set (the Docker image does this), that is used directly.
This is the foundation of the staged `/workspace` layout in the image.

### `api/schemas.py`
Pydantic v2 request and response models. `ApiResponse` is the success
envelope used by every route: `{success: true, data: {...}, error: null}`.
`ErrorEnvelope` is what the exception handler returns. `Role` is a
`Literal["admin", "ops", "analyst"]`.

### `api/routes/health.py`
- `GET /health` - liveness; always returns `{status: "ok"}`.
- `GET /ready` - readiness; invokes `inference.service.engine.is_ready()`
  and surfaces the model path and feature order. This is the endpoint
  Docker Compose uses as the health check.

### `api/routes/kpis.py`
`GET /api/v1/kpis` reads the KPI config via `engine.kpi_config.load_kpi_document()`
and returns the readiness metrics and the Kent-Leg + north-star blocks.
`require_role("analyst", ...)`.

### `api/routes/viability.py`
`POST /api/v1/viability/evaluate` accepts an `EvaluateRequest` carrying
the market profile, historical data, external data, and optional scenario
overrides. Delegates to
[api/viability_service.py](../../backend/api/viability_service.py) which
runs `engine.pipeline.Pipeline().run()`, classifies readiness, derives the
tier, and folds the ML prediction into the response.

### `api/routes/inference_routes.py`
- `GET /api/v1/inference/meta` - model path, feature order, `is_ready`,
  decision threshold, version.
- `POST /api/v1/inference/predict` - takes the 9 features as a flat JSON
  payload (`InferenceRequest`) and returns `{p_ready, label}`.

### `api/routes/upload_jobs.py`
Accepts a single `.xlsx` multipart upload, validates the OOXML zip
magic, writes it into a temp work directory, and kicks off
`run_upload_job` as a background task. Job status is polled via
`GET /api/v1/jobs/{job_id}`. Rate-limited to 10/min for uploads and
120/min for polling.

### `api/routes/metrics_admin.py`
`GET /api/v1/admin/metrics` returns the in-memory metrics collector state
(request counts by route, error counts). `require_role("admin", ...)`.

### `api/routes/operations_demo.py`
Entirely optional. CRUD fixtures for bookings, dispatch assignments,
payments, profiles, notifications. Only registered when
`RYW_ENABLE_OPERATIONS_DEMO=true`. Used by the design team to flesh out
the Operations UX.

### `api/upload_pipeline.py`
Coordinates the upload job:

- `_ensure_scripts_importable()` adds `code/` to `sys.path` so
  `scripts.build_phase1_canonical_base` resolves.
- `_default_intake_workbooks(repo_root)` returns paths under `code/inputs/`.
- `run_upload_job(job_id, q1_path, work_dir)` calls each step, updating the
  job store with `received`, `validate`, `phase1`, `normalize`, `pipeline`,
  `done` step markers. Failures set `error` with the exception text.

### `api/viability_service.py`
Wraps `engine.pipeline.Pipeline` with the readiness classifier and
confidence tier. Also emits `lineage_refs` pointing at
`code/intermediates (regenerable phase artifacts pruned)/*.csv` so the UI can link back to the
traceability files.

### `api/jobs_store.py`
In-memory `JobStore` keyed by UUID. Stores per-step status rows and
timestamps. No persistence: restart the backend and jobs disappear.

### `engine/`
Domain logic imported by the API. Top-level modules:

- `models/market.py` - `RegionGeography`, `FleetDeployment`,
  `ProspectiveContract`, `MarketProfile` dataclasses.
- `evaluation/` - `DashboardFormatter`, `classify_readiness`,
  `derive_confidence_tier`, `evaluate_reconstruction_drift`.
- `kpi_config.py` - single point of entry for the KPI JSON. Exposes
  `load_kpi_document`, `readiness_metric_specs`, `feature_order`, and
  `passes_gate(value, threshold, pass_rule)`.
- `input_layer/ingestion.py` - reads the Q1 daily metrics workbook into
  canonical tables.
- `pipeline.py` - orchestrates extraction, feature computation, gate
  evaluation, and returns a `ViabilityReport`.

### `inference/service.py`
Wraps the XGBoost model. `_resolve_model_dir()` reads
`RYW_INFERENCE_MODEL_DIR` (defaults to the bundled directory). The
`ExplainableInferenceEngine` loads the model file on first use, caches
the feature order from metadata, and exposes `predict(features_dict)`
returning `InferenceResult(p_ready, label, explanation)`.

## Frontend

### `nuxt.config.ts`
- `runtimeConfig.backendBaseUrl` resolves from `NUXT_BACKEND_BASE_URL` or
  `BACKEND_BASE_URL` with a `127.0.0.1:8000` dev fallback.
- `runtimeConfig.internalApiSecret` resolves from
  `NUXT_INTERNAL_API_SECRET` or `RYW_INTERNAL_API_SECRET`.
- Nuxt is pinned at `^3.17.5`.

### `server/api/backend/[...path].ts`
Nitro proxy route that forwards any request under `/api/backend/*` to the
backend, preserving method, body, and `X-Role`; injects
`X-Internal-Secret` when configured; normalizes 502s into a JSON envelope
so the UI can show "API unreachable" instead of a generic network error.

### `composables/useBackendApi.ts`
- `role` - reactive ref, persisted to `localStorage`.
- `apiGet`, `apiPost`, `apiUpload` - thin wrappers around `$fetch` that
  set `X-Role` and surface backend errors as `Error` with a `.statusCode`.

### `composables/useViabilitySession.ts`
Keys used to stash evaluation results across page transitions:
`RYW_STORAGE_MARKET` (current market profile) and `RYW_STORAGE_HISTORICAL`
(the most recent `/viability/evaluate` response).

### `composables/useAppTheme.ts`
Toggles `html[data-theme]`. Persists to `localStorage`. Default is
`dark`.

### `layouts/default.vue`
Shared SPA shell described in
[architecture/spa-layout.md](./spa-layout.md).

### `pages/*`
Each page hydrates its data from `useBackendApi()` + `useViabilitySession()`.
Page-local state (filter selections, expanded accordions) is in local
`ref()`s.

### `components/*`
See [frontend/component-catalog.md](../frontend/component-catalog.md) for
the full catalog.

## Offline pipeline

### `scripts/build_phase1_canonical_base.py`
Inputs: the three xlsx workbooks under `code/inputs/`. Outputs: canonical
CSVs under `code/intermediates (regenerable phase artifacts pruned)/` plus `phase1_summary.json` and a
field dictionary.

### `scripts/generate_readiness_training_rows.py`
Generates three stratified populations:

- **Bulk** - broad draws from historical distributions.
- **Boundary** - rows tightly clustered around each gate threshold.
- **Flip** - pairs of rows that differ by a single feature crossed above
  and below its threshold.

Outputs: `code/intermediates (regenerable training artifacts pruned)/readiness_training_rows.csv`.

### `scripts/build_readiness_training_base.py`
Joins the training rows with phase-1-derived summary stats, applies gate
rules to compute `label_ready`, and writes the canonical training base
to `code/intermediates/inference_inputs/readiness_training_base.csv`.

### `inference_engine/scripts/sync_inputs_from_phase1.py`
Copies `phase1/` into `inference_inputs/` and writes `MANIFEST.json` and
`MANIFEST.upstream.json` capturing input SHAs. Notebooks then read from
the snapshot instead of the live `phase1/` directory.

### `inference_engine/scripts/train_readiness_model_from_inputs.py`
Fits `XGBClassifier`, evaluates on a held-out split, calibrates with
Platt scaling, exports `xgboost_readiness_inputs_v1/` under
`code/outputs/models/`.

### `inference_engine/scripts/test_readiness_edge_cases.py`
Runs the T1..T6 sensitivity suite against a given model. See
[ml/sensitivity-harness.md](../ml/sensitivity-harness.md).
