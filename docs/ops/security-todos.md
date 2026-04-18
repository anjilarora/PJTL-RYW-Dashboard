# Security TODOs for production

This doc is the canonical home for the "before we deploy to real users"
checklist. The same items appear in the startup warning emitted by
`api/app.py` when `RYW_ENV=production` is combined with demo defaults.

## Demo defaults you must change

| Item | Why it is unsafe | Fix |
|---|---|---|
| `RYW_AUTH_MODE=header` | Any client can set `X-Role: admin`. There is no verification. | Set `RYW_AUTH_MODE=jwt` and wire a real IdP. The role comes from the signed token's `role` claim. |
| Empty `RYW_CORS_ORIGINS` | Defaults to localhost + `frontend:3000`. Browsers will block legitimate prod origins and demo origins might accidentally work. | Set it to your comma-separated deployed frontend origins. |
| Missing `RYW_INTERNAL_API_SECRET` | The API is reachable from anywhere on its port, bypassing the Nitro proxy. | Set a 32-byte random string on both the backend and the frontend (`NUXT_INTERNAL_API_SECRET`). |
| `RYW_EXPOSE_INTERNAL_ERRORS=true` | Stack traces leak into the API response. | Keep the default `false` in production. |
| `RYW_ENABLE_OPERATIONS_DEMO=true` | Mounts the in-memory CRUD surface with no persistence or auditing. | Set `false` in production. |
| In-memory job store | Job records vanish on restart. Fine for demo, not for audit. | Swap the store implementation to Redis/Postgres. The `JobStore` interface in `api/jobs_store.py` is the seam. |
| Mutable bundled model under `/app/` | Anyone with write access to the image can swap models silently. | Sign the model directory (SHA tree) during CI and validate at startup. |

## Deploy-day configuration

```
RYW_ENV=production
RYW_AUTH_MODE=jwt
RYW_JWT_SECRET=<from IdP>
RYW_JWT_ALGORITHM=RS256       # or HS256 if your IdP signs symmetrically
RYW_CORS_ORIGINS=https://readiness.example.com
RYW_INTERNAL_API_SECRET=<32+ bytes random>
RYW_ENABLE_OPERATIONS_DEMO=false
RYW_EXPOSE_INTERNAL_ERRORS=false
RYW_LOG_LEVEL=INFO
```

On the frontend:

```
NUXT_BACKEND_BASE_URL=https://backend.internal.example.com
NUXT_INTERNAL_API_SECRET=<same as RYW_INTERNAL_API_SECRET>
```

## Observability

- Every request gets a `X-Request-Id` (added if absent) via
  [middleware/request_context.py](../../backend/api/middleware/request_context.py).
- 500 responses include the `request_id` in the error envelope; operators
  can correlate.
- Configure your log aggregator to pull `ryw-backend` and
  `ryw-frontend` container stdout. The backend emits structured lines
  for upload pipeline milestones (`upload_job_received`,
  `upload_job_validate_ok`, etc.).

## Data handling

- No PII ever enters the system in the demo workbooks; the Q1 daily
  metrics are fleet-level aggregates.
- If you later ingest rider-level data, make sure:
  - `.xlsx` uploads are virus-scanned before the backend reaches them.
  - The `tempfile.mkdtemp()` work directory is on an encrypted volume.
  - Logs do not capture row contents.

## Vendor surface

- PyPI: `fastapi`, `uvicorn`, `pydantic`, `pydantic-settings`, `slowapi`,
  `xgboost`, `joblib`, `openpyxl`, `PyJWT`. Subscribe to their security
  advisories.
- npm: `nuxt`. Subscribe to Nuxt security advisories.
- Docker base images: `python:3.12-slim`, `node:22-alpine`. Rebuild
  weekly.

## Related reading

- [api/roles-and-auth.md](../api/roles-and-auth.md)
- [ops/docker.md](./docker.md)
- [production-checklist.md](../production-checklist.md)
