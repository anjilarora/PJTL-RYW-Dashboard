# pjtl-ride-yourway
A market launch viability and decision system for Ride YourWay, a non-emergency medical transportation provider.

## Backend API

The backend exposes a FastAPI service with:
- Viability evaluation endpoint
- Booking, dispatch, payment, profile, admin settings, and notifications endpoints

Machine learning and model training live in **`code/inference_engine/`** (not in this package).

- **Demo auth:** `X-Role` header (`analyst`, `ops`, `admin`). **Not a trust boundary** — use `RYW_AUTH_MODE=jwt` in production ([docs/jwt-auth.md](docs/jwt-auth.md)).
- **Production checklist:** [../docs/production-checklist.md](../docs/production-checklist.md) (CORS, internal secret, errors exposure, persistence).
- **Architecture:** [../../docs/architecture/hld.md](../../docs/architecture/hld.md)

### Run

```bash
python -m pip install -e .[dev]
uvicorn api.main:app --reload --port 8000
```

### Test

```bash
pytest
```

### OpenAPI

Run the server and use **`GET /openapi.json`** (or `/docs`). The static `openapi.yaml` may drift; regenerate from the running app when needed.

### Docker

Run from the `code/` directory (where `docker-compose.yml` lives):

```bash
cd code
docker compose up -d --build
```

The UI is mapped to host port **3010** by default (`http://127.0.0.1:3010`) so it does not clash with other apps on **3000**. Override with `RYW_FRONTEND_PORT=3001` if you prefer.

The Nuxt container must reach the API via the Docker service hostname; compose sets **`NUXT_BACKEND_BASE_URL=http://backend:8000`** (plain `BACKEND_BASE_URL` is not applied at runtime by Nuxt).

### Sliders page sensitivity contract

The XGBoost readiness classifier that powers `/api/v1/inference/predict` (consumed by the sliders on the landing page) must satisfy:

> For every gate `g` with threshold `T` and pass rule `{gte, lte, gt, lt}`, letting `eps = max(|T| * 0.01, 1e-4)`, a single-gate nudge from `T + eps` (pass side) to `T - eps` (fail side) - holding the other eight gates at a comfortable-pass midpoint - must flip the prediction from **Ready** to **Not Ready**.

This is enforced by [`code/inference_engine/scripts/test_readiness_edge_cases.py`](../inference_engine/scripts/test_readiness_edge_cases.py) (suites T1-T6). The training driver [`train_readiness_model_from_inputs.py`](../inference_engine/scripts/train_readiness_model_from_inputs.py) invokes `run_suite(..., strict=True)` after export and exits non-zero on any failure, so "trained" always means "passes the contract".

Retraining end-to-end:

```bash
source code/inference_engine/.venv/bin/activate
python code/scripts/generate_readiness_training_rows.py
python code/scripts/build_readiness_training_base.py
python code/inference_engine/scripts/sync_inputs_from_phase1.py
python code/inference_engine/scripts/train_readiness_model_from_inputs.py
# Integration check through the FastAPI layer:
cd code/backend && pytest -q tests/test_inference_edge_cases.py
```
