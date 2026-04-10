"""Map viability dashboard report conditions to XGBoost inference feature dict."""

from __future__ import annotations

from typing import Any, Dict

_METRIC_TO_FEATURE = {
    1: "vehicle_utilization",
    2: "billed_utilization",
    3: "total_volume_pool",
    4: "revenue_per_kent_leg",
    5: "high_acuity_share",
    6: "non_billable_noshow",
    7: "road_hours_per_vehicle",
    8: "contract_concentration",
    9: "cost_per_road_hour",
}


def report_dict_to_inference_features(report: Dict[str, Any]) -> Dict[str, float]:
    """Build inference payload from formatter `report` block (conditions list)."""
    out: Dict[str, float] = {}
    for cond in report.get("conditions", []):
        m = int(cond["metric"])
        key = _METRIC_TO_FEATURE.get(m)
        if key:
            out[key] = float(cond["actual"])
    missing = [k for k in _METRIC_TO_FEATURE.values() if k not in out]
    if missing:
        raise ValueError(f"Report missing metrics needed for ML: {missing}")
    return out
