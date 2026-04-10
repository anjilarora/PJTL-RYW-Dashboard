from __future__ import annotations

from typing import Any, Dict


def evaluate_reconstruction_drift(
    historical_data: Dict[str, Any],
    report_payload: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Lightweight reconstruction drift evaluator.
    Compares report-level values against available historical anchors when present.
    """
    report = report_payload.get("report", {})
    projected_margin = float(report.get("projected_margin", 0.0))
    passing = int(report.get("passing", 0))
    failing = int(report.get("failing", 0))

    weekly_margin_rows = historical_data.get("weekly_margin", [])
    historical_margin = 0.0
    if isinstance(weekly_margin_rows, list) and weekly_margin_rows:
        parsed = []
        for row in weekly_margin_rows:
            try:
                parsed.append(float(row.get("margin_pct", 0.0)))
            except (AttributeError, TypeError, ValueError):
                continue
        if parsed:
            historical_margin = sum(parsed) / len(parsed)

    margin_drift = abs(projected_margin - historical_margin)
    drift_status = "within_tolerance" if margin_drift <= 0.10 else "out_of_tolerance"

    # unresolved-gate proxy for insufficient-data routing
    unresolved_gate_proxy = max(0, 9 - (passing + failing))

    return {
        "historical_margin_anchor": historical_margin,
        "projected_margin": projected_margin,
        "margin_drift_abs": margin_drift,
        "drift_status": drift_status,
        "unresolved_gate_proxy": unresolved_gate_proxy,
        "recommendation": (
            "use_assumption_backed_confidence"
            if drift_status == "out_of_tolerance"
            else "retain_current_confidence"
        ),
    }
