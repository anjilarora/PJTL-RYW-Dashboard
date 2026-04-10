# Production deployment checklist

## Security

- Use JWT auth (`RYW_AUTH_MODE=jwt`) with a real IdP; `X-Role` is demo-only.
- Set `RYW_CORS_ORIGINS` to your deployed frontend origin(s).
- Set `RYW_INTERNAL_API_SECRET` when the API is not exposed only to a trusted proxy.
- Keep `RYW_EXPOSE_INTERNAL_ERRORS=false` in production (default).

## Persistence

- Operations data is in-memory; use a database for persistence.

## Readiness model retraining

The XGBoost classifier behind the sliders page must satisfy the sensitivity contract documented in [`code/backend/README.md`](../backend/README.md#sliders-page-sensitivity-contract): a 1%-of-threshold change at any single gate must flip the Ready/Not-Ready decision.

- Never ship a readiness model that was trained outside `code/inference_engine/scripts/train_readiness_model_from_inputs.py`; that driver runs `test_readiness_edge_cases.py` in strict mode post-export and exits non-zero if the contract is violated.
- `test_readiness_edge_cases.py` must also be run manually any time the KPI gate definitions in [`code/config/pjtl_kpis_and_formulas.json`](../config/pjtl_kpis_and_formulas.json) change, to catch cases where the shipped model no longer agrees with the updated thresholds.
- The FastAPI integration check `pytest code/backend/tests/test_inference_edge_cases.py` should be part of the deploy pipeline; it catches regressions in route wiring (payload schema, classification threshold) that a pure-model harness misses.
