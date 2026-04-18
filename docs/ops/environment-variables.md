# Environment variables

All environment variables are either backend (`RYW_*`) or frontend
(`NUXT_*`). Nuxt only re-reads variables prefixed with `NUXT_` at runtime;
the frontend Dockerfile and `nuxt.config.ts` reflect this.

## Backend (`RYW_*`)

Loaded by [code/backend/api/config.py](../../backend/api/config.py) via
`pydantic-settings`.

| Variable | Default | Description |
|---|---|---|
| `RYW_ENV` | `development` | `development`, `staging`, or `production`. Controls startup warnings and error verbosity. |
| `RYW_AUTH_MODE` | `header` | `header` (demo) or `jwt`. |
| `RYW_JWT_SECRET` | *none* | Required when `RYW_AUTH_MODE=jwt`. |
| `RYW_JWT_ALGORITHM` | `HS256` | JWT decode algorithm. |
| `RYW_JWT_ROLE_CLAIM` | `role` | Claim name that carries the role. |
| `RYW_CORS_ORIGINS` | *empty* | Comma-separated origins. Empty uses localhost + compose defaults. |
| `RYW_INTERNAL_API_SECRET` | *empty* | Enables `X-Internal-Secret` enforcement when set. |
| `RYW_ENABLE_OPERATIONS_DEMO` | `true` | Registers the `/api/v1/operations/*` router. Turn off in production. |
| `RYW_RATE_LIMIT_EVALUATE` | `60/minute` | Rate limit for `/api/v1/viability/evaluate`. |
| `RYW_RATE_LIMIT_PREDICT` | `120/minute` | Rate limit for `/api/v1/inference/predict`. |
| `RYW_LOG_LEVEL` | `INFO` | Python logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`). |
| `RYW_EXPOSE_INTERNAL_ERRORS` | `false` | If true, 500 responses include the exception text. Never true in production. |
| `RYW_REPO_ROOT` | *none* | Override the repo-root walk. Docker image sets this to `/workspace`. |
| `RYW_INFERENCE_MODEL_DIR` | bundled | Override the model directory. Docker image sets it to `/app/inference_models`. |

## Frontend (`NUXT_*`)

Loaded by [code/frontend/nuxt.config.ts](../../frontend/nuxt.config.ts)
via `runtimeConfig`.

| Variable | Default | Description |
|---|---|---|
| `NUXT_BACKEND_BASE_URL` | `http://127.0.0.1:8000` | Where the Nitro proxy forwards `/api/backend/*` traffic. In compose it is `http://backend:8000`. |
| `NUXT_INTERNAL_API_SECRET` | *empty* | Forwarded as `X-Internal-Secret`. Must match `RYW_INTERNAL_API_SECRET` on the backend. |
| `BACKEND_BASE_URL` | *empty* | Build-time fallback. Only read if `NUXT_BACKEND_BASE_URL` is unset. Kept for legacy dev setups. |
| `RYW_INTERNAL_API_SECRET` | *empty* | Secondary fallback for the secret; matches the backend var for convenience. |

## Compose port overrides

| Variable | Default | Used by |
|---|---|---|
| `RYW_FRONTEND_PORT` | `3010` | Host port exposed by `frontend` in `docker-compose.yml`. |

## Why the `NUXT_` prefix matters

Nuxt's runtime config only reads env vars prefixed with `NUXT_` at
runtime. Setting `BACKEND_BASE_URL` alone works for `nuxt dev` because
that is a build-time evaluation, but it will **not** flow into the
compiled Nitro server. The frontend Dockerfile builds once, and the
compose file injects `NUXT_BACKEND_BASE_URL` at runtime because that is
what Nuxt actually honors post-build.

## Example `.env` for local compose

```
# shell where you run `docker compose up`
RYW_ENV=development
# Leave auth mode at header for demos
RYW_AUTH_MODE=header
# Optional: force internal-secret
# RYW_INTERNAL_API_SECRET=change-me
# RYW_FRONTEND_PORT=3010
```

The compose file reads these via `${VAR:-default}` substitution.

## Example production `.env`

```
RYW_ENV=production
RYW_AUTH_MODE=jwt
RYW_JWT_SECRET=<from IdP>
RYW_CORS_ORIGINS=https://readiness.example.com
RYW_INTERNAL_API_SECRET=<32+ random bytes>
RYW_ENABLE_OPERATIONS_DEMO=false
RYW_EXPOSE_INTERNAL_ERRORS=false
```

Do not commit real production secrets. The repo's `.gitignore` excludes
`.env`, but always verify before pushing.
