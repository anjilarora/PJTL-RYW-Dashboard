# Sensitivity harness (T1..T6)

The sensitivity harness enforces that the shipped readiness classifier
behaves like a well-calibrated, monotonic approximation of the nine-gate
rule. It is defined in
[code/inference_engine/scripts/test_readiness_edge_cases.py](../../inference_engine/scripts/test_readiness_edge_cases.py).

## The contract

A user should be able to:

- Take a baseline "all gates pass" feature vector, nudge a single feature
  by **1% (relative to the threshold) across the threshold**, and see the
  model flip between `Ready` and `Not Ready`.
- Sweep any single slider from its UI minimum to its UI maximum and see
  **exactly one flip** at the threshold.
- Not crash when a slider is pushed to the edge of its allowed range.
- Not flip spuriously on tiny noise once the baseline is safely on the
  pass side.

## The six suites

| Suite | Name | What it checks | Strict? |
|---|---|---|---|
| T1 | Per-gate 1% flip | At each gate, baseline-pass with a 1% downgrade crosses to Not Ready. | yes |
| T2 | Exact threshold | `value == threshold` honors the declared `pass_rule` (`>=`, `<=`, `<`). | advisory |
| T3 | Two-gate interaction | Paired barely-fail / barely-pass across two gates flip consistently. | yes |
| T4 | Slider sweep | Stepping any gate from min to max yields exactly one flip near `T`. | yes |
| T5 | Out-of-range | Sliders at their UI min/max and slightly beyond still classify without exception. | yes |
| T6 | Noise robustness | Small jitter around a barely-pass baseline keeps the label at `Ready`. | yes |

Strict suites block CI. T2 is advisory because it is a measure-zero
condition: the exact-threshold input is a single point that XGBoost's
discrete splits can place on either side. The advisory mode means a T2
miss logs a warning without failing the build.

`STRICT_SUITES: frozenset[str] = frozenset({"T1", "T3", "T4", "T5", "T6"})`

## Slider ranges

The harness uses the same slider min/max that
[code/frontend/pages/index.vue](../../frontend/pages/index.vue) uses so
that T4 and T5 cover exactly what the UI exposes. Updating one side
without the other will cause T5 out-of-range failures.

## How to run

```bash
cd code
python inference_engine/scripts/test_readiness_edge_cases.py \
  --model outputs/models/xgboost_readiness_stage3_v2/xgboost_readiness_model.joblib \
  --metadata outputs/models/xgboost_readiness_stage3_v2/xgboost_readiness_metadata.json \
  --strict
```

Without `--strict` the script reports failures but exits 0. With
`--strict` any strict-suite failure exits 1.

## Expected output shape

```
T1 baseline_all_pass: Ready p=0.9x
T1 <gate_key>_downshift_1pct: flipped (pass -> not ready)
T3 <gate_key_a>+<gate_key_b>: paired_ok
T4 <gate_key>_sweep: flips=1
T5 <gate_key>:{min,max,beyond_min,beyond_max}: classified
T6 <gate_key>:jitter_preserves_ready: all trials Ready

Ran 103 checks: 101 pass, 2 advisory (T2 exact-threshold).
```

## Why advisory

We write the UI to clamp the exact threshold visually as "pass". Getting
XGBoost to respect an exact tie for 100% of checks would require
injecting a deterministic tie-breaking rule on top of the model. That
trade-off (extra code + risk of breaking monotonicity) was deemed worse
than a logged warning.
