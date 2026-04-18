# Build from the `code/` directory: docker compose build backend
# (see code/docker-compose.yml: context `.`, dockerfile: backend/Dockerfile)

FROM python:3.12-slim

WORKDIR /app

COPY backend/pyproject.toml /app/pyproject.toml
COPY backend/api /app/api
COPY backend/engine /app/engine
COPY backend/inference /app/inference

# Exported XGBoost model artifacts (code/outputs/models/; produced by
# `python code/inference_engine/scripts/train_readiness_model_from_inputs.py`).
COPY outputs/models /app/inference_models

# Operational EDA aggregates consumed by code/backend/engine/operational_service.py
# (D1..D10 dashboard endpoints). Produced by
# `python code/inference_engine/scripts/operational_eda.py`.
COPY outputs/reports/operational_eda /workspace/code/outputs/reports/operational_eda

# Shared KPI / gate JSON (engine/kpi_config.py resolves to /config when app root is /app)
COPY config /config

# Pipeline support: api.baseline and api.intake_pipeline import
# scripts.build_phase1_canonical_base and read the bundled Q1 workbook + intake
# templates from <repo_root>/code/inputs. We stage a synthetic repo layout at
# /workspace and point the backend at it via RYW_REPO_ROOT so the existing
# scripts' `code/config/...` marker walk resolves unchanged.
COPY config /workspace/code/config
COPY lib /workspace/code/lib
COPY scripts /workspace/code/scripts
COPY inputs/RideYourWay_Prospective_Market_Intake_Template.xlsx /workspace/code/inputs/RideYourWay_Prospective_Market_Intake_Template.xlsx
COPY inputs/RideYourWay_Prospective_Market_Intake_Example.xlsx /workspace/code/inputs/RideYourWay_Prospective_Market_Intake_Example.xlsx
# Q1 Daily Metrics workbook powers the frozen baseline viability loaded at app startup.
COPY ["inputs/Q1 Daily Metrics 2026.xlsx", "/workspace/code/inputs/Q1 Daily Metrics 2026.xlsx"]

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
