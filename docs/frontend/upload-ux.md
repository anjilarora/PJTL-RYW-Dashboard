# Upload UX

The intake upload surface lives on `pages/dashboard.vue` and gates on
strict rules to keep the backend pipeline happy.

## User flow

1. Analyst clicks "Upload daily-metrics workbook".
2. File picker accepts only `.xlsx` (enforced by both the native
   filter and the backend OOXML zip-magic check).
3. Selecting a file immediately POSTs it to `/api/backend/api/v1/jobs/upload`.
4. The UI shows a step list with spinner/check/cross per step
   (`received`, `validate`, `phase1`, `normalize`, `pipeline`,
   `done`).
5. On `done`, the dashboard auto-selects the freshly-evaluated market
   and pushes it into `useViabilitySession()` so every panel
   re-renders.
6. On `error`, the failing step is highlighted with the server error
   text.

## Constraints (with copy)

- **Excel workbook (.xlsx) only.** CSV is not accepted because the
  phase-1 script expects the multi-sheet layout shipped by the intake
  template.
- **Same shape as the bundled January 2026 example** (Dec 29 2025 -
  Jan 31 2026 window). The validate step verifies sheet names before
  phase-1 runs.
- **Max size**: `MAX_UPLOAD_BYTES` in
  [code/backend/api/upload_pipeline.py](../../backend/api/upload_pipeline.py).
- **Role**: analyst or higher.

## InfoTip body

The circled-i next to the upload button renders a mini-guide:

```
Drop your daily-metrics workbook (.xlsx) here.

What we do with it:
  - code/inputs/ - source workbook (not written to; never modified).
  - code/intermediates/phase1/ - canonical CSVs extracted on the fly
    for this upload only.
  - code/outputs/models/ - the XGBoost model that scores your
    readiness (not regenerated per upload).

We clean up the uploaded copy once the evaluation is done.
```

This replaced earlier copy that leaked internal repo paths in a
customer-facing tone. See
[kpi/assumption-register.md](../kpi/assumption-register.md) for why the
intake is program-keyed (one row per program, not per contract).

## Error handling

- 400 with filename error: "Upload an .xlsx workbook - CSV is not
  supported right now."
- 400 with zip-magic error: "That file does not look like a valid
  Excel workbook. Re-save from Excel and try again."
- 413 (max size): "File too large."
- 500 with request id: "Upload pipeline errored (request id shown).
  Ask the backend ops channel."
- 502 (Nitro -> backend unreachable): "API unreachable. Retry or
  check `docker compose ps`."

## Why the pipeline runs in the background

Phase-1 extraction takes multiple seconds on real workbooks; running
it inline would exceed typical HTTP proxy timeouts and block the UI
event loop. Returning `{job_id}` and polling is cheap and
progress-friendly.

See [api/upload-workflow.md](../api/upload-workflow.md) for the server
side of the same flow.
