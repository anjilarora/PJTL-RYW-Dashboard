# Running locally

Three options, each useful for a different workflow.

## Option 1: Docker Compose (simplest)

From the `code/` directory (same directory as
[docker-compose.yml](../../docker-compose.yml)):

```bash
cd code
docker compose build
docker compose up -d
# Backend:  http://127.0.0.1:8000
# Frontend: http://127.0.0.1:3010
docker compose logs -f
docker compose down
```

Use this when you want the production-equivalent wiring (Nitro proxy,
internal secret, model baked into image). See
[ops/docker.md](./docker.md).

## Option 2: Native dev (fast feedback)

### Backend

```bash
cd code
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e backend
export RYW_AUTH_MODE=header
export RYW_ENV=development
uvicorn api.main:app --reload --host 127.0.0.1 --port 8000
```

### Frontend

In another terminal:

```bash
cd code/frontend
npm ci
export NUXT_BACKEND_BASE_URL=http://127.0.0.1:8000
npm run dev -- --host 127.0.0.1 --port 3000
```

Navigate to `http://127.0.0.1:3000`. The Nitro proxy in the dev server
will call `NUXT_BACKEND_BASE_URL`.

## Option 3: Offline pipeline only

When you are iterating on the ML side without touching the web services.

```bash
cd code
source .venv/bin/activate
python scripts/build_phase1_canonical_base.py
python scripts/generate_readiness_training_rows.py
python scripts/build_readiness_training_base.py
python inference_engine/scripts/sync_inputs_from_phase1.py
python inference_engine/scripts/train_readiness_model_from_inputs.py
python inference_engine/scripts/test_readiness_edge_cases.py --strict
jupyter nbconvert --to notebook --execute \
    inference_engine scripts \
    inference_engine scripts \
    inference_engine scripts
```

After stage-3 re-exports the model, rebuild the backend image:

```bash
docker compose build backend && docker compose up -d backend
```

## Python version

Pinned to 3.12 because the backend Dockerfile uses `python:3.12-slim`.
Later 3.x versions should work but are not exercised in CI.

## Node version

22 LTS, matching `node:22-alpine` in the frontend Dockerfile.

## Virtual env layout

```
code/
  .venv/              <- Python venv, not in git
  backend/pyproject.toml
  frontend/package.json
```

## First-run checklist

1. `code/inputs/Q1 Daily Metrics 2026.xlsx` exists.
2. `code/inputs/RideYourWay_Prospective_Market_Intake_{Template,Example}.xlsx` exist.
3. `code/outputs/models/xgboost_readiness_stage3_v2/xgboost_readiness_model.joblib` exists.
4. `curl http://127.0.0.1:8000/ready` returns `{"data": {"ready": true, ...}}`.
5. UI landing page loads at `http://127.0.0.1:3010/` with the RYW logo.

If any step fails, read
[data-pipeline/overview.md](../data-pipeline/overview.md) "When the
pipeline fails" table.
