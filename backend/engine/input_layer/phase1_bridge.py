"""
Map Phase-1 canonical CSVs (from ``build_phase1_canonical_base``) into the raw
shape expected by :class:`MetricsNormalizer`, then into ``historical_data`` for
:class:`engine.pipeline.Pipeline`.

ML training rows in ``readiness_training_rows.csv`` are PJTL-supplied; this
bridge derives engine-consistent aggregates from extracted workbooks instead.
Distribution parity with the exported XGBoost model is not guaranteed.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path
from typing import Any


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _mode_key(raw: str) -> str:
    m = (raw or "").strip().lower()
    if m in {"wc", "wheelchair"}:
        return "wheelchair"
    if m in {"amb", "ambulatory"}:
        return "ambulatory"
    if m in {"stretcher", "str"}:
        return "stretcher"
    if "secure" in m:
        return "securecare"
    return m or "unknown"


def _float(x: Any, default: float = 0.0) -> float:
    if x in (None, ""):
        return default
    try:
        return float(x)
    except (TypeError, ValueError):
        return default


def phase1_csv_dir_to_raw_ingest(phase1_dir: Path) -> dict[str, Any]:
    """
    Build the dict consumed by ``MetricsNormalizer.normalize()`` from a Phase-1
    output directory.
    """
    contract_path = phase1_dir / "contract_volume_base.csv"
    vehicle_path = phase1_dir / "vehicle_day_base.csv"
    mode_path = phase1_dir / "mode_breakdown_base.csv"
    payer_path = phase1_dir / "payer_summary_base.csv"
    margin_path = phase1_dir / "weekly_margin_base.csv"

    required = [contract_path, vehicle_path, mode_path]
    for p in required:
        if not p.is_file():
            raise FileNotFoundError(f"Phase-1 output missing required file: {p}")

    contract = _read_csv(contract_path)
    vehicle_day = _read_csv(vehicle_path)
    mode_rows = _read_csv(mode_path)
    payer_summary = _read_csv(payer_path)
    margin_rows = _read_csv(margin_path)

    # --- total_performance (one aggregate row feeds VariableMapper averages) ---
    # IMPORTANT: the downstream consumer (VariableMapper._build_baselines) treats
    # "total_rides" and "kent_legs" on this row as *daily* averages. Q1 contract
    # rows cover ~34 service days, so we MUST divide the quarterly totals by the
    # number of distinct service dates; otherwise demand is inflated by ~34x
    # and utilization blows up to 10,000%+ downstream.
    n = len(contract)
    completed = sum(1 for r in contract if (r.get("order_status") or "").strip() == "Completed")
    noshow = sum(1 for r in contract if (r.get("order_status") or "").strip() == "No show")
    canceled = sum(1 for r in contract if (r.get("order_status") or "").strip() == "Canceled")
    total_kl = sum(_float(r.get("kent_legs")) for r in contract)
    total_trips = max(n, 1)
    service_days = {
        (r.get("date_of_service_iso") or r.get("date_of_service") or "").strip()
        for r in contract
    }
    service_days.discard("")
    unique_days = max(1, len(service_days))
    total_performance: list[dict[str, Any]] = [
        {
            "total_rides": float(n) / unique_days,
            "kent_legs": total_kl / unique_days,
            "completion_rate": completed / total_trips,
            "noshow_rate": noshow / total_trips,
            "cancellation_rate": canceled / total_trips,
            "service_days": unique_days,
        }
    ]

    # --- mode_breakdown rows for MetricsNormalizer._normalize_modes ---
    kl_by: dict[str, float] = defaultdict(float)
    rev_by: dict[str, float] = defaultdict(float)
    for r in mode_rows:
        mode = _mode_key(str(r.get("order_mode", "")))
        if mode == "unknown":
            continue
        kl_by[mode] += _float(r.get("kent_legs"))
        rev_by[mode] += _float(r.get("order_price"))
    mode_norm_rows: list[dict[str, Any]] = []
    total_mode_kl = sum(kl_by.values()) or 1.0
    for mode in sorted(kl_by.keys()):
        mode_norm_rows.append(
            {
                "mode": mode,
                "kent_legs": kl_by[mode],
                "revenue": rev_by[mode],
                "pct": kl_by[mode] / total_mode_kl,
            }
        )

    # --- contract_volume (payer / volume) ---
    contract_norm: list[dict[str, Any]] = []
    for r in contract:
        contract_norm.append(
            {
                "payer": r.get("payer_id", ""),
                "order_status": r.get("order_status", ""),
                "kent_legs": r.get("kent_legs", ""),
                "trip_count": r.get("kent_legs", "1"),
            }
        )

    # --- revenue_by_payer from payer_summary ---
    rev_payer: dict[str, dict[str, float]] = defaultdict(lambda: {"revenue": 0.0, "legs": 0.0})
    for r in payer_summary:
        pid = (r.get("payer_id") or "").strip()
        if not pid:
            continue
        rev_payer[pid]["revenue"] += _float(r.get("sum_order_price"))
        rev_payer[pid]["legs"] += _float(r.get("sum_kent_legs"))
    revenue_by_payer: list[dict[str, Any]] = []
    for payer, agg in sorted(rev_payer.items()):
        revenue_by_payer.append(
            {
                "payer": payer,
                "total_revenue": agg["revenue"],
                "kent_legs": agg["legs"],
            }
        )

    # --- weekly_margin: MetricsNormalizer expects revenue / cost per row ---
    weekly_margin: list[dict[str, Any]] = []
    for r in margin_rows:
        weekly_margin.append(
            {
                "revenue": r.get("total_revenue", ""),
                "cost": r.get("total_cost", ""),
            }
        )

    # --- vehicle_breakdown ---
    vehicle_breakdown: list[dict[str, Any]] = []
    for r in vehicle_day:
        vehicle_breakdown.append(
            {
                "date": r.get("date_iso", r.get("date", "")),
                "road_time": r.get("road_time", ""),
                "active_time": r.get("road_time", ""),
                "kent_legs": r.get("kent_legs", ""),
                "revenue": r.get("revenue", ""),
                "mode": r.get("mode", ""),
            }
        )

    return {
        "total_performance": total_performance,
        "regional_performance": [],
        "mode_breakdown": mode_norm_rows,
        "weekly_margin": weekly_margin,
        "vehicle_breakdown": vehicle_breakdown,
        "contract_volume": contract_norm,
        "revenue_by_payer": revenue_by_payer,
    }


def phase1_csv_dir_to_historical_data(phase1_dir: Path) -> dict[str, Any]:
    """Phase-1 directory → ``historical_data`` for :func:`api.viability_service.evaluate_market`."""
    from engine.input_layer.normalization import MetricsNormalizer
    from engine.input_layer.variable_mapping import VariableMapper

    raw = phase1_csv_dir_to_raw_ingest(phase1_dir)
    normalized = MetricsNormalizer().normalize(raw)
    return VariableMapper().map(normalized)
