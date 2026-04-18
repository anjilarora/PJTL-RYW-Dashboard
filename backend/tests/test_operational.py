"""Tests for the /api/v1/dashboard/* operational endpoints.

These rely on the CSV artifacts written by
``code/inference_engine/scripts/operational_eda.py`` being present under
``code/outputs/reports/operational_eda/``. The Docker image bakes them in via
``code/backend/Dockerfile`` stages; developers should run::

    python code/inference_engine/scripts/operational_eda.py

before executing the suite.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from api.main import app
from engine import operational_service as ops


client = TestClient(app)


def _have_artifacts() -> bool:
    return (ops.REPORTS_DIR / "fleet_gate_scorecard.csv").is_file()


pytestmark = pytest.mark.skipif(
    not _have_artifacts(),
    reason="operational_eda CSVs not generated yet; run the script/notebook first",
)


ENDPOINTS = [
    ("fleet-scorecard", "regions"),
    ("weekly-trend", "weeks"),
    ("mode-profitability", "modes"),
    ("otp", "rows"),
    ("payer-concentration", "payers"),
    ("hourly-demand", "rows"),
    ("cancellations", "rows"),
    ("rev-per-kl", "payers"),
    ("securecare-compare", "streams"),
    ("cost-regional", "regions"),
]


@pytest.mark.parametrize("path,top_key", ENDPOINTS)
def test_operational_endpoints_return_data(path: str, top_key: str) -> None:
    resp = client.get(f"/api/v1/dashboard/{path}", headers={"X-Role": "analyst"})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["success"] is True
    assert top_key in body["data"]
    payload = body["data"][top_key]
    # Every top-level container is a non-empty list/dict
    assert payload, f"{path} returned empty {top_key}"


def test_fleet_scorecard_shape() -> None:
    resp = client.get("/api/v1/dashboard/fleet-scorecard", headers={"X-Role": "analyst"})
    regions = resp.json()["data"]["regions"]
    names = {r["region"] for r in regions}
    assert {"Grand Rapids", "Lansing", "Battle Creek"} <= names
    for region in regions:
        assert region["gates"], f"No gate rows for {region['region']}"
        # Each gate row has the expected keys
        for gate in region["gates"]:
            assert {"gate", "label", "target", "comparator", "value", "pass"} <= set(gate.keys())


def test_weekly_trend_has_five_weeks() -> None:
    resp = client.get("/api/v1/dashboard/weekly-trend", headers={"X-Role": "analyst"})
    weeks = resp.json()["data"]["weeks"]
    week_names = [w["week"] for w in weeks]
    assert week_names == ["Week 1", "Week 2", "Week 3", "Week 4", "Week 5"]


def test_payer_concentration_flags_warnings() -> None:
    resp = client.get("/api/v1/dashboard/payer-concentration", headers={"X-Role": "analyst"})
    data = resp.json()["data"]
    # 72 payers in Q1; at least one is flagged as either over-cap or near-cap
    assert len(data["payers"]) > 10
    assert "warnings" in data
    # Cap thresholds are 20%
    assert data["cap_volume"] == 0.20
    assert data["cap_revenue"] == 0.20


def test_rev_per_kl_includes_fleet_rate() -> None:
    resp = client.get("/api/v1/dashboard/rev-per-kl", headers={"X-Role": "analyst"})
    data = resp.json()["data"]
    assert data["target"] == 70.0
    assert data["fleet_rev_per_kentleg"] is not None


def test_securecare_compare_has_both_streams() -> None:
    resp = client.get("/api/v1/dashboard/securecare-compare", headers={"X-Role": "analyst"})
    streams = resp.json()["data"]["streams"]
    assert "Fleet" in streams
    assert "SecureCare" in streams
    for stream in streams.values():
        assert "weeks" in stream
        assert len(stream["weeks"]) >= 1


def test_regional_cost_marked_as_estimate() -> None:
    resp = client.get("/api/v1/dashboard/cost-regional", headers={"X-Role": "analyst"})
    data = resp.json()["data"]
    assert data["is_estimate"] is True
    regions = {r["region"] for r in data["regions"]}
    assert {"Grand Rapids", "Lansing", "Battle Creek"} == regions


def test_missing_artifacts_returns_404(monkeypatch, tmp_path) -> None:
    """When artifacts are absent, endpoints must surface a 404 with guidance."""
    monkeypatch.setattr(ops, "REPORTS_DIR", tmp_path / "does-not-exist")
    resp = client.get("/api/v1/dashboard/fleet-scorecard", headers={"X-Role": "analyst"})
    assert resp.status_code == 404
    detail = resp.json()["detail"]
    assert detail["reason"] == "operational_eda_artifact_missing"
