# Docker and Compose

Local orchestration is handled by
[code/docker-compose.yml](../../docker-compose.yml). Both services are
declared there; each has its own Dockerfile inside `code/`.

## Services

### `backend`

- Built from [code/backend/Dockerfile](../../backend/Dockerfile) with
  `context: .` (the `code/` directory, i.e. the same directory as
  `docker-compose.yml`).
- `python:3.12-slim` base.
- Ships the FastAPI app under `/app/`, the XGBoost model under
  `/app/inference_models/`, and the KPI config under `/config/`.
- Stages a **synthetic repo layout** at `/workspace/code/` so the upload
  pipeline scripts resolve paths identically to local dev. The env var
  `RYW_REPO_ROOT=/workspace` points `api/repo_root.py` at it.
- Exposes `8000:8000`.
- Runs as the non-root `ryw` user.
- Health check: `urllib.request.urlopen('http://127.0.0.1:8000/ready')`.

### `frontend`

- Built from [code/frontend/Dockerfile](../../frontend/Dockerfile) with
  `context: ./frontend` (relative to `code/docker-compose.yml`).
- Two-stage `node:22-alpine` build: `npm ci` + `nuxt build`, then a
  runtime image that runs `node .output/server/index.mjs`.
- Exposes `${RYW_FRONTEND_PORT:-3010}:3000`. Host port defaults to 3010
  so that a native `nuxt dev` on 3000 does not conflict.
- `depends_on.backend.condition: service_healthy`.

## Key commands

```bash
# From the code/ directory (same directory as docker-compose.yml)
docker compose build          # build both images
docker compose up -d          # start in background
docker compose logs -f        # tail logs
docker compose ps             # status
docker compose down           # stop and remove containers
docker compose down --volumes # also drop anonymous volumes
```

To rebuild only the backend after a model change:

```bash
docker compose build backend && docker compose up -d backend
```

## Why the synthetic `/workspace` layout

The upload pipeline calls
`scripts.build_phase1_canonical_base.main()` inside the backend process.
That script resolves inputs via `code_root_from_anchor()`, which walks
up looking for `code/config/`. In the image, the application is
installed at `/app/` with a flattened layout that has no `code/` marker.

Rather than rewrite the scripts to support a second layout, the
Dockerfile copies a minimal mirror:

```
/workspace/
  code/
    config/
    lib/
    scripts/
    inputs/
      RideYourWay_Prospective_Market_Intake_Template.xlsx
      RideYourWay_Prospective_Market_Intake_Example.xlsx
```

and sets `RYW_REPO_ROOT=/workspace`. The scripts find their inputs,
resolve their outputs into the tmp work_dir, and never touch the image
itself.

## Networking

Compose creates a default bridge network. The frontend talks to the
backend at `http://backend:8000` via `NUXT_BACKEND_BASE_URL`. Host-side
traffic hits the frontend at `http://127.0.0.1:3010`.

For `X-Internal-Secret` enforcement, set `RYW_INTERNAL_API_SECRET` in
the shell that runs compose; both services read it through the
environment mapping.

## Volumes and data persistence

There are **no bind mounts for data** by default. Every uploaded
workbook lives inside a tmp work_dir that gets cleaned up when the job
ends. If you want to persist job artifacts for auditing, mount a host
path into the container and point the upload pipeline at it.

## Common issues

| Symptom | Fix |
|---|---|
| `frontend` container restarts in a loop | Check `docker compose logs frontend`. Typical cause: `NUXT_BACKEND_BASE_URL` unreachable at startup. Restart once the backend is healthy. |
| `/ready` returns 503 inside the container | The model directory is empty. Confirm `code/outputs/models/xgboost_readiness_stage3_v2/` exists on the host before `docker compose build backend`. |
| `502 API unreachable` in the UI | The Nitro proxy could not reach the backend. Check `docker compose ps` and confirm `backend` is `healthy`. |
| `403 Forbidden` on the upload page | `RYW_INTERNAL_API_SECRET` is set on the backend but not on the frontend (or vice versa). Set both or neither. |
