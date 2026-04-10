"""HTTP-level sensitivity checks for the sliders page.

Mirrors a subset of the T1 contract from
``code/inference_engine/scripts/test_readiness_edge_cases.py``, exercising the
same XGBoost artifact through the FastAPI route rather than loading the model
directly. Catches integration-layer regressions (payload schema, response
shape, classification threshold wiring) that a pure model harness would miss.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api.main import app
from engine.kpi_config import readiness_metric_specs

client = TestClient(app)

# Comfortable-pass baselines chosen well inside each gate's passing half; all
# nine must jointly pass so any single-gate flip is unambiguous.
COMFORT_VALUES: dict[str, float] = {
    "vehicle_utilization": 1.10,
    "billed_utilization": 1.20,
    "total_volume_pool": 1.40,
    "revenue_per_kent_leg": 90.0,
    "high_acuity_share": 0.12,
    "non_billable_noshow": 0.04,
    "road_hours_per_vehicle": 10.5,
    "contract_concentration": 0.12,
    "cost_per_road_hour": 40.0,
}


def _eps(threshold: float) -> float:
    return max(abs(threshold) * 0.01, 1e-4)


def _barely_pass(threshold: float, pass_rule: str) -> float:
    return threshold + _eps(threshold) if pass_rule in ("gte", "gt") else threshold - _eps(threshold)


def _barely_fail(threshold: float, pass_rule: str) -> float:
    return threshold - _eps(threshold) if pass_rule in ("gte", "gt") else threshold + _eps(threshold)


def _predict(payload: dict) -> dict:
    resp = client.post(
        "/api/v1/inference/predict", json=payload, headers={"X-Role": "analyst"}
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["data"]


def test_baseline_all_pass_is_ready() -> None:
    data = _predict(COMFORT_VALUES)
    assert data["prediction"] == "Ready", json.dumps(data, indent=2)


@pytest.mark.parametrize("spec", readiness_metric_specs(), ids=lambda s: s["key"])
def test_single_gate_barely_pass_is_ready(spec: dict) -> None:
    payload = {**COMFORT_VALUES, spec["key"]: _barely_pass(float(spec["threshold"]), spec["pass_rule"])}
    data = _predict(payload)
    assert data["prediction"] == "Ready", (
        f"{spec['key']} barely-pass expected Ready; got {data['prediction']} "
        f"(p={data['probability_ready']:.4f})"
    )


@pytest.mark.parametrize("spec", readiness_metric_specs(), ids=lambda s: s["key"])
def test_single_gate_barely_fail_is_not_ready(spec: dict) -> None:
    payload = {**COMFORT_VALUES, spec["key"]: _barely_fail(float(spec["threshold"]), spec["pass_rule"])}
    data = _predict(payload)
    assert data["prediction"] == "Not Ready", (
        f"{spec['key']} barely-fail expected Not Ready; got {data['prediction']} "
        f"(p={data['probability_ready']:.4f})"
    )


def test_response_shape_exposes_threshold_and_drivers() -> None:
    data = _predict(COMFORT_VALUES)
    assert "classification_threshold" in data
    assert 0.0 <= data["probability_ready"] <= 1.0
    assert isinstance(data.get("top_drivers"), list)
