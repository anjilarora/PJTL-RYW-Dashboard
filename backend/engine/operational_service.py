"""Load operational-EDA CSV aggregates for the dashboard API.

The script ``code/inference_engine/scripts/operational_eda.py`` is the
single source of truth and writes outputs under
``code/outputs/reports/operational_eda/``. This service only **reads** those
CSVs and massages them into response payloads. Rerun the script to refresh.
"""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

from api.repo_root import repo_root


REPORTS_DIR = repo_root() / "code" / "outputs" / "reports" / "operational_eda"
PLOTS_DIR = repo_root() / "code" / "outputs" / "plots" / "operational_eda"

# Gate thresholds — used when decorating scorecard responses with pass/fail.
GATE_TARGETS: Dict[str, Dict[str, Any]] = {
    "g1_vehicle_utilization": {"target": 0.95, "comparator": "ge", "label": "Vehicle utilization"},
    "g2_billed_utilization": {"target": 1.05, "comparator": "ge", "label": "Billed utilization"},
    "g3_volume_pool": {"target": 1.20, "comparator": "ge", "label": "Volume pool ratio"},
    "g4_rev_per_kentleg": {"target": 70.0, "comparator": "ge", "label": "Revenue / Kent-Leg"},
    "g5_higher_acuity_mix": {"target": 0.05, "comparator": "ge", "label": "Higher-acuity mix"},
    "g6_nonbillable_ns": {"target": 0.10, "comparator": "le", "label": "Non-billable no-shows"},
    "g7_road_time": {"target": 9.0, "comparator": "ge", "label": "Road time / vehicle / day"},
    "g8_largest_payer_vol": {"target": 0.20, "comparator": "le", "label": "Largest payer (volume)"},
    "g8_largest_payer_rev": {"target": 0.20, "comparator": "le", "label": "Largest payer (revenue)"},
    "g8_contract_concentration": {"target": 0.20, "comparator": "le", "label": "Payer concentration"},
    "g9_cost_per_road_hour": {"target": 50.0, "comparator": "le", "label": "Cost per road hour"},
}


class OperationalDataMissing(Exception):
    """Raised when a required CSV artifact is absent (notebook never ran)."""


def _csv_path(name: str) -> Path:
    return REPORTS_DIR / name


def _read_csv(name: str) -> List[Dict[str, str]]:
    path = _csv_path(name)
    if not path.is_file():
        try:
            display = str(path.relative_to(repo_root()))
        except ValueError:
            display = str(path)
        raise OperationalDataMissing(
            f"Missing operational EDA artifact: {display}. "
            f"Run `python code/inference_engine/scripts/operational_eda.py` to regenerate."
        )
    with path.open(newline="") as fh:
        return list(csv.DictReader(fh))


def _float(v: Any) -> Optional[float]:
    if v is None or v == "":
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    if math.isnan(f) or math.isinf(f):
        return None
    return f


def _int(v: Any) -> Optional[int]:
    f = _float(v)
    return int(f) if f is not None else None


def _bool(v: Any) -> Optional[bool]:
    if v in ("", None):
        return None
    s = str(v).strip().lower()
    if s in ("true", "1", "yes"):
        return True
    if s in ("false", "0", "no"):
        return False
    return None


def _gate_pass(gate_id: str, value: Optional[float]) -> Optional[bool]:
    if value is None:
        return None
    spec = GATE_TARGETS.get(gate_id)
    if not spec:
        return None
    target = float(spec["target"])
    if spec["comparator"] == "ge":
        return value >= target
    return value <= target


# ---------------------------------------------------------------------------
# D1 — Fleet scorecard
# ---------------------------------------------------------------------------


def fleet_scorecard() -> Dict[str, Any]:
    rows = _read_csv("fleet_gate_scorecard.csv")
    out: Dict[str, List[Dict[str, Any]]] = {}
    for r in rows:
        region = r["region"]
        out.setdefault(region, []).append({
            "gate": r["gate"],
            "label": r.get("label") or GATE_TARGETS.get(r["gate"], {}).get("label", r["gate"]),
            "target": _float(r.get("target")),
            "comparator": r.get("comparator"),
            "value": _float(r.get("value")),
            "pass": _bool(r.get("pass")),
            "detail": r.get("detail") or None,
        })
    return {
        "regions": [
            {"region": region, "gates": gates}
            for region, gates in out.items()
        ]
    }


# ---------------------------------------------------------------------------
# D2 — Weekly trend
# ---------------------------------------------------------------------------


WEEKLY_COLUMNS = [
    "vehicle_usage",
    "billed_usage",
    "volume_pool_ratio",
    "otp",
    "revenue_per_kentleg",
    "higher_acuity_mix",
    "nonbillable_ns_rate",
    "largest_payer_vol",
    "largest_payer_rev",
    "total_revenue",
    "total_cost",
    "profit_margin",
]


def weekly_trend() -> Dict[str, Any]:
    rows = _read_csv("weekly_gate_trend.csv")
    out = []
    for r in rows:
        entry: Dict[str, Any] = {"week": r["week"]}
        for col in WEEKLY_COLUMNS:
            entry[col] = _float(r.get(col))
            entry[f"{col}_wow"] = _float(r.get(f"{col}_wow"))
        entry["largest_payer_vol_name"] = r.get("largest_payer_vol_name") or None
        entry["largest_payer_rev_name"] = r.get("largest_payer_rev_name") or None
        out.append(entry)
    return {"weeks": out}


# ---------------------------------------------------------------------------
# D3 — Mode profitability
# ---------------------------------------------------------------------------


def mode_profitability() -> Dict[str, Any]:
    rows = _read_csv("mode_profitability.csv")
    out = []
    for r in rows:
        out.append({
            "mode": r["mode"],
            "trip_count": _int(r.get("trip_count")),
            "trip_share": _float(r.get("trip_share")),
            "kent_legs": _float(r.get("kent_legs")),
            "kent_leg_share": _float(r.get("kent_leg_share")),
            "revenue": _float(r.get("revenue")),
            "revenue_share": _float(r.get("revenue_share")),
            "avg_revenue_per_trip": _float(r.get("avg_revenue_per_trip")),
            "avg_revenue_per_kentleg": _float(r.get("avg_revenue_per_kentleg")),
            "avg_miles": _float(r.get("avg_miles")),
            "nonbillable_ns_rate": _float(r.get("nonbillable_ns_rate")),
            "billable_ns_rate": _float(r.get("billable_ns_rate")),
            "profit_margin": _float(r.get("profit_margin")),
            "total_cost": _float(r.get("total_cost")),
            "note": r.get("note") or None,
        })
    return {"modes": out}


# ---------------------------------------------------------------------------
# D4 — OTP matrix
# ---------------------------------------------------------------------------


def otp_matrix() -> Dict[str, Any]:
    rows = _read_csv("otp_matrix.csv")
    out = []
    for r in rows:
        out.append({
            "scope": r["scope"],
            "region": r["region"],
            "leg": r["leg"],
            "day": r["day"],
            "otp": _float(r.get("otp")),
        })
    return {"rows": out}


# ---------------------------------------------------------------------------
# D5 — Payer concentration
# ---------------------------------------------------------------------------


def payer_concentration() -> Dict[str, Any]:
    rows = _read_csv("payer_concentration.csv")
    payers = []
    for r in rows:
        payers.append({
            "payer_id": r["payer_id"],
            "kent_legs": _float(r.get("kent_legs")),
            "revenue": _float(r.get("revenue")),
            "trips": _int(r.get("trips")),
            "vol_share": _float(r.get("vol_share")),
            "rev_share": _float(r.get("rev_share")),
            "over_20pct_vol": _bool(r.get("over_20pct_vol")),
            "over_20pct_rev": _bool(r.get("over_20pct_rev")),
            "near_cap": _bool(r.get("near_cap")),
        })
    payers.sort(key=lambda p: p.get("rev_share") or 0, reverse=True)
    warnings = [p for p in payers if p.get("over_20pct_vol") or p.get("over_20pct_rev") or p.get("near_cap")]
    return {
        "payers": payers,
        "warnings": warnings,
        "cap_volume": 0.20,
        "cap_revenue": 0.20,
    }


# ---------------------------------------------------------------------------
# D6 — Hourly demand / idle
# ---------------------------------------------------------------------------


def hourly_demand() -> Dict[str, Any]:
    rows = _read_csv("hourly_demand_idle.csv")
    out = []
    for r in rows:
        out.append({
            "day": r["day"],
            "hour": r["hour"],
            "value": _float(r.get("value")),
            "metric": r.get("metric"),
            "is_idle_business": _bool(r.get("is_idle_business")),
        })
    idle = [r for r in out if r.get("is_idle_business") and r.get("metric") == "completed"]
    return {"rows": out, "idle_windows": idle}


# ---------------------------------------------------------------------------
# D7 — Cancellation patterns
# ---------------------------------------------------------------------------


def cancellations(top_n: int = 50) -> Dict[str, Any]:
    rows = _read_csv("cancellation_patterns.csv")
    parsed = []
    for r in rows:
        parsed.append({
            "order_status": r.get("order_status"),
            "reason": r.get("reason"),
            "payer_id": r.get("payer_id"),
            "order_mode": r.get("order_mode"),
            "day": r.get("day"),
            "count": _int(r.get("count")) or 0,
        })
    parsed.sort(key=lambda x: x["count"], reverse=True)

    # Aggregates for compact dashboard display
    by_reason: Dict[str, int] = {}
    by_mode: Dict[str, int] = {}
    by_day: Dict[str, int] = {}
    by_payer: Dict[str, int] = {}
    for r in parsed:
        by_reason[r["reason"] or "Unknown"] = by_reason.get(r["reason"] or "Unknown", 0) + r["count"]
        by_mode[r["order_mode"] or "Unknown"] = by_mode.get(r["order_mode"] or "Unknown", 0) + r["count"]
        by_day[r["day"] or "Unknown"] = by_day.get(r["day"] or "Unknown", 0) + r["count"]
        by_payer[r["payer_id"] or "Unknown"] = by_payer.get(r["payer_id"] or "Unknown", 0) + r["count"]

    def _topn(d: Dict[str, int], n: int = 10) -> List[Dict[str, Any]]:
        return [{"key": k, "count": v} for k, v in sorted(d.items(), key=lambda kv: kv[1], reverse=True)[:n]]

    return {
        "rows": parsed[:top_n],
        "by_reason": _topn(by_reason, 20),
        "by_mode": _topn(by_mode, 10),
        "by_day": _topn(by_day, 10),
        "by_payer": _topn(by_payer, 10),
        "total": sum(r["count"] for r in parsed),
    }


# ---------------------------------------------------------------------------
# D8 — Revenue per Kent-Leg
# ---------------------------------------------------------------------------


def rev_per_kentleg() -> Dict[str, Any]:
    rows = _read_csv("payer_rev_per_kentleg.csv")
    payers = []
    for r in rows:
        payers.append({
            "payer_id": r["payer_id"],
            "revenue": _float(r.get("revenue")),
            "kent_legs": _float(r.get("kent_legs")),
            "trips": _int(r.get("trips")),
            "revenue_per_kentleg": _float(r.get("revenue_per_kentleg")),
            "lift_vs_70": _float(r.get("lift_vs_70")),
        })
    payers.sort(key=lambda p: p.get("kent_legs") or 0, reverse=True)

    total_rev = sum((p.get("revenue") or 0) for p in payers)
    total_kl = sum((p.get("kent_legs") or 0) for p in payers)
    fleet_rate = (total_rev / total_kl) if total_kl else None

    return {
        "payers": payers,
        "target": 70.0,
        "fleet_rev_per_kentleg": fleet_rate,
    }


# ---------------------------------------------------------------------------
# D9 — SecureCare vs fleet compare
# ---------------------------------------------------------------------------


def securecare_compare() -> Dict[str, Any]:
    rows = _read_csv("cost_margin_trend.csv")
    streams: Dict[str, List[Dict[str, Any]]] = {}
    for r in rows:
        streams.setdefault(r["stream"], []).append({
            "week": r["week"],
            "total_revenue": _float(r.get("total_revenue")),
            "total_cost": _float(r.get("total_cost")),
            "profit_margin": _float(r.get("profit_margin")),
        })

    summary = {}
    for stream, items in streams.items():
        rev = sum((i["total_revenue"] or 0) for i in items)
        cost = sum((i["total_cost"] or 0) for i in items)
        summary[stream] = {
            "total_revenue": rev,
            "total_cost": cost,
            "net_margin": rev - cost,
            "margin_pct": (rev - cost) / rev if rev else None,
            "weeks": items,
        }
    return {"streams": summary}


# ---------------------------------------------------------------------------
# D10 — Regional cost estimate
# ---------------------------------------------------------------------------


def regional_cost() -> Dict[str, Any]:
    rows = _read_csv("regional_cost_estimate.csv")
    out = []
    for r in rows:
        out.append({
            "region": r["region"],
            "vehicle_count": _int(r.get("vehicle_count")),
            "cost_share_assumed": _float(r.get("cost_share_assumed")),
            "estimated_cost": _float(r.get("estimated_cost")),
            "estimated_road_hours": _float(r.get("estimated_road_hours")),
            "estimated_cost_per_road_hour": _float(r.get("estimated_cost_per_road_hour")),
            "note": r.get("note"),
        })
    return {
        "regions": out,
        "target_cost_per_road_hour": 50.0,
        "is_estimate": True,
    }


# ---------------------------------------------------------------------------
# Shared manifest (used by ops surface)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Manifest:
    csvs: List[str]
    plots: List[str]
    summary: Dict[str, Any]


@lru_cache(maxsize=1)
def manifest() -> Manifest:
    import json

    path = REPORTS_DIR / "manifest.json"
    if not path.is_file():
        return Manifest(csvs=[], plots=[], summary={})
    data = json.loads(path.read_text())
    return Manifest(
        csvs=data.get("csv_artifacts", []),
        plots=data.get("plot_artifacts", []),
        summary=data.get("summary", {}),
    )


__all__ = [
    "OperationalDataMissing",
    "fleet_scorecard",
    "weekly_trend",
    "mode_profitability",
    "otp_matrix",
    "payer_concentration",
    "hourly_demand",
    "cancellations",
    "rev_per_kentleg",
    "securecare_compare",
    "regional_cost",
    "manifest",
    "Manifest",
]
