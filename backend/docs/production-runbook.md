# Production Runbook

## Health and readiness

- **`GET /health`** — process up; includes inference snapshot.
- **`GET /ready`** — returns **503** if the XGBoost model or metadata is missing or invalid. Use for orchestrator / load balancer probes.

## Configuration (environment)

| Variable | Purpose |
| --- | --- |
| `RYW_INFERENCE_MODEL_DIR` | Directory containing `xgboost_readiness.json` and `xgboost_readiness_metadata.json`. |
| `RYW_ENV` | `development` \| `staging` \| `production` (affects log level). |
| `RYW_CORS_ORIGINS` | Comma-separated browser origins; defaults include localhost. |
| `RYW_INTERNAL_API_SECRET` | If set, requires matching `X-Internal-Secret` on `/api/v1/*` (Nuxt proxy should send it). |
| `RYW_AUTH_MODE` | `header` (demo) or `jwt` — see [jwt-auth.md](./jwt-auth.md). |
| `RYW_JWT_SECRET` | Required for `jwt` mode (HS256). |

## Observability

- Request logs: JSON lines with `request_id`, `path`, `method`, `status_code`, `duration_ms`.
- Track viability readiness states and ML prediction rates.
- Alert on `/ready` failures and elevated 5xx rates.

## Security

- Prefer **`RYW_AUTH_MODE=jwt`** behind TLS; do not rely on `X-Role` in production.
- Rate limits apply to `POST /api/v1/viability/evaluate` and `POST /api/v1/inference/predict` (see `slowapi` defaults in code).
- Validate payloads via Pydantic models; keep secrets in env or a secret manager.

## Reliability

- **In-memory store** (`api/store.py`) is **demo-only** — replace with durable storage if operations endpoints are real.
- Model directory should be mounted read-only in containers.

## Performance

- Benchmark `POST /api/v1/viability/evaluate` with representative payloads before go-live.
