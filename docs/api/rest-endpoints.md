# REST endpoints

All paths are relative to the backend base URL
(`http://127.0.0.1:8000` in local dev, `http://backend:8000` inside the
compose network, whatever you have proxied in prod). Every route under
`/api/v1/*` is guarded by `get_role` (either `X-Role` header or JWT
depending on `RYW_AUTH_MODE`).

## Envelope

All success responses use `ApiResponse`:

```json
{
  "success": true,
  "data": { ... },
  "error": null
}
```

All errors use the same envelope with `success: false`, `data: {}`, and
`error: { code, message, details }`. See
[code/backend/api/schemas.py](../../backend/api/schemas.py).

## Health (no role required)

### `GET /health`
Always returns 200 with `{status: "ok"}`. Liveness probe only.

### `GET /ready`
Returns 200 when the XGBoost model has been successfully loaded and the
feature order matches the config. Returns 503 otherwise. Docker Compose
uses this as the backend health check.

Response `data`:
```json
{
  "ready": true,
  "model_version": "xgboost_readiness_stage3_v2",
  "feature_order": ["vehicle_utilization", ...],
  "model_dir": "/app/inference_models/xgboost_readiness_stage3_v2"
}
```

## KPIs

### `GET /api/v1/kpis`
**Role**: `analyst` or higher.
Returns the readiness metric catalog, Kent-Leg constants, and the
north-star block exactly as shipped in
[code/config/pjtl_kpis_and_formulas.json](../../config/pjtl_kpis_and_formulas.json).

## Viability

### `POST /api/v1/viability/evaluate`
**Role**: `analyst`.
**Rate limit**: 60/min per IP.

Request body (see `EvaluateRequest`):

```json
{
  "market_profile": {
    "region": { ... },
    "fleet": { ... },
    "overbooking_limit": 1.2,
    "projection_horizon": "quarter",
    "broker_volume_pct": 0.30,
    "prospective_contracts": [ ... ]
  },
  "historical_data": { ... },
  "external_data": null,
  "scenario_overrides": null
}
```

Response `data` contains the nine-gate report, the readiness
classification, the confidence tier, and `lineage_refs` pointing at
`code/intermediates (regenerable phase artifacts pruned)/` artifacts for the UI trace links.

## Inference

### `GET /api/v1/inference/meta`
**Role**: `analyst`.
Returns the currently loaded model metadata - version, feature order,
decision threshold, and `is_ready`.

### `POST /api/v1/inference/predict`
**Role**: `analyst`.
**Rate limit**: 120/min per IP.

Flat JSON body (**not wrapped in `features`**):

```json
{
  "vehicle_utilization": 0.97,
  "billed_utilization": 1.08,
  "total_volume_pool": 1.25,
  "revenue_per_kent_leg": 72.0,
  "high_acuity_share": 0.06,
  "non_billable_noshow": 0.07,
  "road_hours_per_vehicle": 9.4,
  "contract_concentration": 0.18,
  "cost_per_road_hour": 48.0
}
```

Response `data`:
```json
{
  "p_ready": 0.93,
  "label": "Ready",
  "model_version": "xgboost_readiness_stage3_v2"
}
```

## Upload jobs

### `POST /api/v1/jobs/upload`
**Role**: `analyst`.
**Rate limit**: 10/min.

Multipart form field `file`: the `.xlsx` workbook. The server validates
the `.xlsx` extension and the OOXML zip magic bytes, then runs the
pipeline as a background task. Returns `{job_id}` immediately.

### `GET /api/v1/jobs/{job_id}`
**Role**: `analyst`.
**Rate limit**: 120/min.

Returns the job record with one entry per step:

- `received`
- `validate`
- `phase1`
- `normalize`
- `pipeline`
- `done` (or `error`)

See [api/upload-workflow.md](./upload-workflow.md) for the step-by-step
lifecycle.

## Admin

### `GET /api/v1/admin/metrics`
**Role**: `admin`.
Returns the in-memory request/error counter state from
[api/metrics.py](../../backend/api/metrics.py).

## Operations demo (optional)

### `RYW_ENABLE_OPERATIONS_DEMO=true` -> `/api/v1/operations/*`
Only present when the env flag is enabled. Implements CRUD fixtures for
bookings, dispatch assignments, payments, profiles, and notification
events. Intended for the product design team to explore the Operations
UX. Not part of the analyst-facing readiness flow.
