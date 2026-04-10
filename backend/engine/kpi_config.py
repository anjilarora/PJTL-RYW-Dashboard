"""Load shared PJTL KPI / gate definitions from code/config/pjtl_kpis_and_formulas.json."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

_CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "pjtl_kpis_and_formulas.json"


def kpi_config_path() -> Path:
    return _CONFIG_PATH


@lru_cache(maxsize=1)
def load_kpi_document() -> dict[str, Any]:
    if not _CONFIG_PATH.is_file():
        raise FileNotFoundError(f"Missing KPI config: {_CONFIG_PATH}")
    return json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))


def viability_kwargs() -> dict[str, Any]:
    """Keyword args for ViabilityThresholds from JSON."""
    data = load_kpi_document()
    out: dict[str, Any] = {}
    for m in data["readiness_metrics"]:
        out[m["threshold_field"]] = float(m["threshold"])
    out["target_operating_margin"] = float(data["north_star"]["target_operating_margin"])
    return out


def kent_leg_kwargs() -> dict[str, Any]:
    data = load_kpi_document()
    k = data["kent_leg"]
    return {
        "base_miles": float(k["base_miles"]),
        "incremental_miles": float(k["incremental_miles"]),
        "min_kent_legs": float(k["min_kent_legs"]),
    }


def readiness_metric_specs() -> list[dict[str, Any]]:
    """Ordered list of nine gate specs (includes pass_rule, key, threshold)."""
    data = load_kpi_document()
    return sorted(data["readiness_metrics"], key=lambda x: int(x["metric_number"]))


def feature_order() -> list[str]:
    return [m["key"] for m in readiness_metric_specs()]


def passes_gate(value: float, threshold: float, pass_rule: str) -> bool:
    """Match engine.evaluation.viability pass logic for training labels."""
    if pass_rule == "gte":
        return value >= threshold
    if pass_rule == "lte":
        return value <= threshold
    if pass_rule == "lt":
        return value < threshold
    if pass_rule == "gt":
        return value > threshold
    raise ValueError(f"Unknown pass_rule: {pass_rule}")
