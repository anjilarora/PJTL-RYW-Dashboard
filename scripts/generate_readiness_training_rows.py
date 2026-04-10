#!/usr/bin/env python3
"""Regenerate code/intermediates/training/readiness_training_rows.csv with three row populations.

The XGBoost classifier on the sliders page must satisfy a tight sensitivity
contract: a 1%-of-threshold change at any single gate, holding the other
eight on their comfortable passing side, must flip the Ready/Not-Ready
decision (see ``code/inference_engine/scripts/test_readiness_edge_cases.py``).

To shape the decision surface around each gate threshold, this generator
emits three populations:

  * BULK (default 60%) - balanced ready/not-ready markets drawn from wide
    passing / failing ranges, identical in spirit to the prior generator.
  * BOUNDARY CLOUD (default 30%) - for each of the nine gates, rows where
    that gate is drawn from a narrow band around its threshold (both sides)
    while the other eight sit comfortably on their passing side. Forces
    tree splits exactly at the gate threshold.
  * SINGLE-GATE FLIP PAIRS (default 10%) - for each gate, ordered
    (barely-pass, barely-fail) pairs at +/- 1% of the threshold with other
    gates comfortably passing. These are the exact rows the T1 flip test
    probes at inference time.

Every row is labeled with the strict 9-gate AND rule from
``code/config/pjtl_kpis_and_formulas.json`` so the label is a deterministic
function of the features.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np

_CODE = Path(__file__).resolve().parents[1]
if str(_CODE) not in sys.path:
    sys.path.insert(0, str(_CODE))
from lib.repo_paths import code_root_from_anchor

CODE_ROOT = code_root_from_anchor(Path(__file__).parent)
KPI_DOC = CODE_ROOT / "config" / "pjtl_kpis_and_formulas.json"
OUT_CSV = CODE_ROOT / "intermediates" / "training" / "readiness_training_rows.csv"

DEFAULT_ROW_COUNT = 4000
BULK_FRACTION = 0.60
BOUNDARY_FRACTION = 0.30
FLIP_FRACTION = 0.10
READY_FRACTION = 0.5  # within BULK
RANDOM_SEED = 42

# Per-feature sampling ranges. Min/max match the frontend slider ranges so the
# training distribution covers everywhere a user can drag to.
FEATURE_RANGES: dict[str, tuple[float, float]] = {
    "vehicle_utilization": (0.50, 1.45),
    "billed_utilization": (0.50, 1.45),
    "total_volume_pool": (0.50, 2.00),
    "revenue_per_kent_leg": (25.0, 125.0),
    "high_acuity_share": (0.0, 0.35),
    "non_billable_noshow": (0.0, 0.35),
    "road_hours_per_vehicle": (4.0, 16.0),
    "contract_concentration": (0.05, 0.75),
    "cost_per_road_hour": (28.0, 85.0),
}


def _eps(threshold: float) -> float:
    return max(abs(threshold) * 0.01, 1e-4)


def _comfortable_pass(feature: str, threshold: float, rule: str) -> float:
    """Midpoint of the passing half of the slider range for a given feature."""
    lo, hi = FEATURE_RANGES[feature]
    if rule in ("gte", "gt"):
        pass_lo, pass_hi = threshold + _eps(threshold), hi
    else:
        pass_lo, pass_hi = lo, threshold - _eps(threshold)
    return (pass_lo + pass_hi) / 2.0


def _passes(value: float, threshold: float, rule: str) -> bool:
    if rule == "gte":
        return value >= threshold
    if rule == "lte":
        return value <= threshold
    if rule == "gt":
        return value > threshold
    if rule == "lt":
        return value < threshold
    raise ValueError(f"Unknown pass_rule: {rule}")


def _load_kpis() -> list[dict]:
    doc = json.loads(KPI_DOC.read_text(encoding="utf-8"))
    metrics = sorted(doc["readiness_metrics"], key=lambda x: int(x["metric_number"]))
    return [
        {"key": m["key"], "threshold": float(m["threshold"]), "pass_rule": m["pass_rule"]}
        for m in metrics
    ]


def _sample_side(
    rng: np.random.Generator,
    feature: str,
    threshold: float,
    rule: str,
    *,
    pass_side: bool,
) -> float:
    """Draw a value strictly on the requested side of the gate threshold."""
    lo, hi = FEATURE_RANGES[feature]
    eps = (hi - lo) * 1e-4  # numeric guard against strict inequalities
    if rule in ("gte", "gt"):
        pass_low = threshold + (0.0 if rule == "gte" else eps)
        pass_high = hi
        fail_low = lo
        fail_high = threshold - eps
    elif rule in ("lte", "lt"):
        pass_low = lo
        pass_high = threshold - (0.0 if rule == "lte" else eps)
        fail_low = threshold + eps
        fail_high = hi
    else:
        raise ValueError(f"Unknown pass_rule: {rule}")
    band_lo, band_hi = (pass_low, pass_high) if pass_side else (fail_low, fail_high)
    if band_hi <= band_lo:
        return float(threshold)
    return float(rng.uniform(band_lo, band_hi))


def _sample_near_threshold(
    rng: np.random.Generator,
    feature: str,
    threshold: float,
    rule: str,
    *,
    band_halfwidth_eps: float,
) -> float:
    """Uniform sample within +/- band_halfwidth_eps of the threshold, clamped to slider range."""
    lo, hi = FEATURE_RANGES[feature]
    halfwidth = band_halfwidth_eps * _eps(threshold)
    band_lo = max(lo, threshold - halfwidth)
    band_hi = min(hi, threshold + halfwidth)
    if band_hi <= band_lo:
        return float(threshold)
    return float(rng.uniform(band_lo, band_hi))


# ---- Population builders ---------------------------------------------------


def _build_bulk_row(rng: np.random.Generator, metrics: list[dict], ready: bool) -> dict[str, float]:
    """Balanced global-coverage row: all pass, or K>=1 randomly-chosen gates fail."""
    row: dict[str, float] = {}
    if ready:
        for m in metrics:
            row[m["key"]] = _sample_side(rng, m["key"], m["threshold"], m["pass_rule"], pass_side=True)
    else:
        k = int(rng.integers(1, len(metrics) + 1))
        fail_idx = set(rng.choice(len(metrics), size=k, replace=False).tolist())
        for i, m in enumerate(metrics):
            row[m["key"]] = _sample_side(
                rng,
                m["key"],
                m["threshold"],
                m["pass_rule"],
                pass_side=(i not in fail_idx),
            )
    return row


def _build_boundary_row(
    rng: np.random.Generator,
    metrics: list[dict],
    focus_idx: int,
    *,
    band_halfwidth_eps: float = 5.0,
) -> dict[str, float]:
    """One gate sampled in a narrow band around its threshold; others comfortably pass."""
    row: dict[str, float] = {}
    for i, m in enumerate(metrics):
        if i == focus_idx:
            row[m["key"]] = _sample_near_threshold(
                rng, m["key"], m["threshold"], m["pass_rule"], band_halfwidth_eps=band_halfwidth_eps
            )
        else:
            row[m["key"]] = _comfortable_pass(m["key"], m["threshold"], m["pass_rule"])
    return row


def _build_flip_pair(metrics: list[dict], focus_idx: int) -> tuple[dict[str, float], dict[str, float]]:
    """(+1%, -1%) single-gate flip pair with other gates comfortably passing."""
    focus = metrics[focus_idx]
    eps = _eps(focus["threshold"])
    if focus["pass_rule"] in ("gte", "gt"):
        pass_val = focus["threshold"] + eps
        fail_val = focus["threshold"] - eps
    else:
        pass_val = focus["threshold"] - eps
        fail_val = focus["threshold"] + eps
    pass_row: dict[str, float] = {}
    fail_row: dict[str, float] = {}
    for i, m in enumerate(metrics):
        if i == focus_idx:
            pass_row[m["key"]] = pass_val
            fail_row[m["key"]] = fail_val
        else:
            comfy = _comfortable_pass(m["key"], m["threshold"], m["pass_rule"])
            pass_row[m["key"]] = comfy
            fail_row[m["key"]] = comfy
    return pass_row, fail_row


def _label(row: dict[str, float], metrics: list[dict]) -> int:
    return int(all(_passes(row[m["key"]], m["threshold"], m["pass_rule"]) for m in metrics))


def main(row_count: int = DEFAULT_ROW_COUNT) -> None:
    if not KPI_DOC.is_file():
        raise SystemExit(f"Missing KPI config: {KPI_DOC}")
    metrics = _load_kpis()
    n_gates = len(metrics)

    rng = np.random.default_rng(RANDOM_SEED)

    bulk_target = int(round(row_count * BULK_FRACTION))
    boundary_target = int(round(row_count * BOUNDARY_FRACTION))
    flip_target = row_count - bulk_target - boundary_target  # remainder

    rows: list[dict[str, float]] = []

    # 1) BULK - 50/50 ready/not-ready
    ready_count = int(round(bulk_target * READY_FRACTION))
    ready_mask = np.zeros(bulk_target, dtype=bool)
    ready_mask[:ready_count] = True
    rng.shuffle(ready_mask)
    for ready in ready_mask:
        rows.append(_build_bulk_row(rng, metrics, bool(ready)))

    # 2) BOUNDARY CLOUD - evenly distributed across the nine gates
    per_gate = boundary_target // n_gates
    remainder = boundary_target - per_gate * n_gates
    for gate_idx in range(n_gates):
        extras = 1 if gate_idx < remainder else 0
        for _ in range(per_gate + extras):
            rows.append(_build_boundary_row(rng, metrics, gate_idx))

    # 3) FLIP PAIRS - evenly distributed; pair counts as 2 rows
    pair_budget = flip_target // 2
    per_gate_pairs = pair_budget // n_gates
    remainder_pairs = pair_budget - per_gate_pairs * n_gates
    for gate_idx in range(n_gates):
        extras = 1 if gate_idx < remainder_pairs else 0
        for _ in range(per_gate_pairs + extras):
            pair_pass, pair_fail = _build_flip_pair(metrics, gate_idx)
            rows.append(pair_pass)
            rows.append(pair_fail)
    # Top up to exact target with additional flip pairs if parity left us short
    while len(rows) < row_count:
        gate_idx = int(rng.integers(0, n_gates))
        pair_pass, pair_fail = _build_flip_pair(metrics, gate_idx)
        rows.append(pair_pass)
        if len(rows) < row_count:
            rows.append(pair_fail)

    rng.shuffle(rows)

    fieldnames = [m["key"] for m in metrics] + ["label_ready_reference"]
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    pos = 0
    with OUT_CSV.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            label = _label(row, metrics)
            if label:
                pos += 1
            row["label_ready_reference"] = label
            writer.writerow(row)

    neg = len(rows) - pos
    print(
        f"Wrote {OUT_CSV} ({len(rows)} rows; bulk={bulk_target}, boundary={boundary_target}, "
        f"flip={flip_target}; {pos} positive / {neg} negative under strict gate rule)"
    )


if __name__ == "__main__":
    main()
