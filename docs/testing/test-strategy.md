# Test strategy

Tests live in two places: `code/backend/tests/` for Python and the
sensitivity harness in `code/inference_engine/scripts/`. The frontend is
validated via manual smoke tests and the accessibility snapshot tool
(`browser_snapshot`) while running the full stack.

## Python unit and integration tests

Directory: [code/backend/tests/](../../backend/tests/).

- [test_api.py](../../backend/tests/test_api.py) - FastAPI route
  integration tests against the in-memory store. Covers:
  - `/health`, `/ready`
  - Role-guard behavior (`analyst` hitting an `admin` route returns
    403; missing `X-Role` defaults to `analyst`).
  - `/api/v1/viability/evaluate` happy path and the role gate.
  - `/api/v1/jobs/upload` end-to-end on the bundled example workbook.
- [test_inference_edge_cases.py](../../backend/tests/test_inference_edge_cases.py) -
  thin wrapper that imports the sensitivity harness and exercises it
  as a pytest test, so a `pytest` invocation covers the ML contract
  too.
- [test_phase1_bridge.py](../../backend/tests/test_phase1_bridge.py) -
  verifies the upload pipeline bridge: given the bundled workbook,
  the extracted phase-1 CSVs have the expected columns and row counts.

Run with:

```bash
cd code
source .venv/bin/activate
pytest backend/tests -q
```

## Sensitivity harness

[code/inference_engine/scripts/test_readiness_edge_cases.py](../../inference_engine/scripts/test_readiness_edge_cases.py).
See [ml/sensitivity-harness.md](../ml/sensitivity-harness.md) for the
T1..T6 contract.

Run both as a CI gate (strict) and as part of `pytest`:

```bash
python inference_engine/scripts/test_readiness_edge_cases.py \
    --model outputs/models/xgboost_readiness_stage3_v2/xgboost_readiness_model.joblib \
    --metadata outputs/models/xgboost_readiness_stage3_v2/xgboost_readiness_metadata.json \
    --strict
```

## Frontend validation

We do not yet run a headless browser test suite. Validation has three
layers:

1. **Type checks** via `vue-tsc` (implicit in `nuxt build`). The build
   fails on any type error.
2. **Manual smoke tests** with `docker compose up -d`:
   - Landing page renders logo and tabs.
   - Market page upload flow accepts `.xlsx`, starts a job, and shows job progress.
   - Dashboard loads with status pill, gate carousel, and operational deep-dive tabs.
   - Upload pipeline succeeds on the bundled example workbook.
   - Light/dark theme toggles without illegible text.
3. **Accessibility snapshots** via the IDE's MCP browser tools when a
   large UI refactor lands. This catches missing `aria-*` attributes
   and wrong button roles.

## Regression guardrails

- The stage-3 notebook re-exports the model; CI re-runs the harness
  after the export to catch drift.
- Every generated JSON under `code/outputs/` is checked into git, so a
  PR that changes the model without meaning to shows a diff.
- `code/intermediates/inference_inputs/MANIFEST*.json` carry input SHAs so
  surprise input changes surface as provenance diffs in PRs.

## What is not tested (yet)

- End-to-end upload path from the Nuxt UI through a real browser.
- Rate-limit behavior under contention (we test the decorator is
  attached, not the bucket accounting).
- `RYW_AUTH_MODE=jwt` mode - we rely on `PyJWT` and exercise the
  header mode directly.
- Multi-user concurrent upload races on the in-memory job store.
