# Build from repository root: docker compose build backend
# (see docker-compose.yml: context `.`, dockerfile: code/backend/Dockerfile)

FROM python:3.12-slim

WORKDIR /app

COPY code/backend/pyproject.toml /app/pyproject.toml
COPY code/backend/api /app/api
COPY code/backend/engine /app/engine
COPY code/backend/inference /app/inference

# Exported XGBoost model artifacts (code/outputs/models/; produced by
# `python code/inference_engine/scripts/train_readiness_model_from_inputs.py`).
COPY code/outputs/models /app/inference_models

# Shared KPI / gate JSON (engine/kpi_config.py resolves to /config when app root is /app)
COPY code/config /config

# Upload pipeline support: the FastAPI /api/v1/jobs/upload route imports
# scripts.build_phase1_canonical_base and reads the intake workbooks from
# <repo_root>/code/inputs. We stage a synthetic repo layout at /workspace and
# point the backend at it via RYW_REPO_ROOT so the existing scripts'
# `code/config/...` marker walk resolves unchanged.
COPY code/config /workspace/code/config
COPY code/lib /workspace/code/lib
COPY code/scripts /workspace/code/scripts
COPY code/inputs/RideYourWay_Prospective_Market_Intake_Template.xlsx /workspace/code/inputs/RideYourWay_Prospective_Market_Intake_Template.xlsx
COPY code/inputs/RideYourWay_Prospective_Market_Intake_Example.xlsx /workspace/code/inputs/RideYourWay_Prospective_Market_Intake_Example.xlsx

ENV RYW_INFERENCE_MODEL_DIR=/app/inference_models \
    RYW_REPO_ROOT=/workspace

RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir . \
    && groupadd --system ryw && useradd --system --no-create-home --gid ryw ryw \
    && chown -R ryw:ryw /app /config /workspace

USER ryw

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/ready')"

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
