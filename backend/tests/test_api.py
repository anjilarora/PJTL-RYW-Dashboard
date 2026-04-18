import time
import zipfile
from io import BytesIO
from pathlib import Path

from fastapi.testclient import TestClient

from api.main import app
from api.repo_root import repo_root


client = TestClient(app)


INTAKE_EXAMPLE_PATH = (
    repo_root() / "code" / "inputs" / "RideYourWay_Prospective_Market_Intake_Example.xlsx"
)


def _minimal_invalid_q1_xlsx() -> bytes:
    """Zip with xl/workbook.xml but no required Q1 sheet names."""
    buf = BytesIO()
    workbook_xml = b"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
  xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets><sheet name="Only" sheetId="1" r:id="rId1"/></sheets>
</workbook>"""
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("xl/workbook.xml", workbook_xml)
    return buf.getvalue()


def _poll_job(job_id: str, timeout_seconds: float = 60.0) -> dict:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        detail = client.get(f"/api/v1/jobs/{job_id}", headers={"X-Role": "analyst"})
        assert detail.status_code == 200
        body = detail.json()["data"]
        if body["status"] in {"completed", "failed"}:
            return body
        time.sleep(0.25)
    raise AssertionError(f"Job {job_id} did not settle within {timeout_seconds}s")


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "ok"
    assert response.json()["data"]["inference"]["model_loaded"] is True


def test_ready():
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "ready"
    assert response.json()["data"]["inference"]["model_loaded"] is True


def test_viability_evaluate_works():
    payload = {
        "market_profile": {
            "region": {"region_name": "Test Region", "state": "MI"},
            "fleet": {
                "wheelchair_vehicles": 1,
                "ambulatory_vehicles": 1,
                "stretcher_vehicles": 0,
                "securecare_vehicles": 0,
                "drivers": 2,
            },
            "prospective_contracts": [],
        },
        "historical_data": {},
    }
    response = client.post("/api/v1/viability/evaluate", json=payload, headers={"X-Role": "analyst"})
    assert response.status_code == 200
    assert "report" in response.json()["data"]
    assert response.json()["data"]["readiness_state"] in {"Ready", "Not Ready", "Insufficient Data"}
    assert "gate_details" in response.json()["data"]
    assert "governance" in response.json()["data"]
    assert "reconstruction_drift" in response.json()["data"]
    assert "ml_readiness" in response.json()["data"]
    assert "prediction" in response.json()["data"]["ml_readiness"]


def test_inference_predict():
    payload = {
        "vehicle_utilization": 0.98,
        "billed_utilization": 1.08,
        "total_volume_pool": 1.25,
        "revenue_per_kent_leg": 74.0,
        "high_acuity_share": 0.07,
        "non_billable_noshow": 0.08,
        "road_hours_per_vehicle": 9.3,
        "contract_concentration": 0.18,
        "cost_per_road_hour": 48.0,
    }
    response = client.post("/api/v1/inference/predict", json=payload, headers={"X-Role": "analyst"})
    assert response.status_code == 200
    assert response.json()["data"]["prediction"] in {"Ready", "Not Ready"}
    assert "model_version" in response.json()["data"]
    assert "classification_threshold" in response.json()["data"]


def test_inference_meta():
    response = client.get("/api/v1/inference/meta", headers={"X-Role": "analyst"})
    assert response.status_code == 200
    data = response.json()["data"]
    assert "classification_threshold" in data
    assert "model_loaded" in data


def test_kpis():
    response = client.get("/api/v1/kpis", headers={"X-Role": "analyst"})
    assert response.status_code == 200
    assert "readiness_metrics" in response.json()["data"]


def test_job_not_found():
    response = client.get("/api/v1/jobs/00000000-0000-0000-0000-000000000000", headers={"X-Role": "analyst"})
    assert response.status_code == 404


def test_intake_upload_rejects_non_zip_body():
    files = {
        "file": (
            "fake.xlsx",
            b"this-is-not-a-zip-file",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    }
    response = client.post(
        "/api/v1/jobs/intake-upload", files=files, headers={"X-Role": "analyst"}
    )
    assert response.status_code == 400


def test_legacy_upload_route_is_gone():
    files = {
        "file": (
            "fake.xlsx",
            b"PK\x03\x04",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    }
    response = client.post("/api/v1/jobs/upload", files=files, headers={"X-Role": "analyst"})
    # The POST is either unknown (404) or resolves to the job-detail GET route
    # with the wrong method (405); either way, daily-metrics upload is gone.
    assert response.status_code in {404, 405}


def test_admin_metrics_requires_admin():
    denied = client.get("/api/v1/admin/metrics", headers={"X-Role": "analyst"})
    assert denied.status_code == 403
    ok = client.get("/api/v1/admin/metrics", headers={"X-Role": "admin"})
    assert ok.status_code == 200
    data = ok.json()["data"]
    assert "total_requests" in data
    assert "by_status" in data
    assert "top_paths" in data


def test_ops_booking_creates_in_app_notification():
    payload = {"rider_name": "NoteUser", "pickup": "A", "dropoff": "B", "mode": "ambulatory"}
    create = client.post("/api/v1/bookings", json=payload, headers={"X-Role": "ops"})
    assert create.status_code == 200
    notes = client.get("/api/v1/notifications", headers={"X-Role": "analyst"})
    assert notes.status_code == 200
    items = notes.json()["data"]["items"]
    assert any("NoteUser" in str(i.get("message", "")) for i in items)


def test_intake_upload_fails_workbook_validation():
    content = _minimal_invalid_q1_xlsx()
    files = {
        "file": (
            "bad.xlsx",
            content,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    }
    response = client.post(
        "/api/v1/jobs/intake-upload", files=files, headers={"X-Role": "analyst"}
    )
    assert response.status_code == 200
    job_id = response.json()["data"]["job_id"]
    body = _poll_job(job_id)
    assert body["status"] == "failed"
    assert "Intake workbook missing sheets" in (body["error"] or "")


def test_viability_baseline_returns_cached_q1_payload():
    response = client.get("/api/v1/viability/baseline", headers={"X-Role": "analyst"})
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["readiness_state"] in {"Ready", "Not Ready", "Insufficient Data"}
    conditions = data["report"].get("conditions") or []
    assert len(conditions) > 0, "Baseline viability should include gate conditions"
    assert "ml_readiness" in data
    follow_up = client.get("/api/v1/viability/baseline", headers={"X-Role": "analyst"})
    assert follow_up.status_code == 200
    assert follow_up.json()["data"]["readiness_state"] == data["readiness_state"]


def test_viability_baseline_gate_magnitudes_are_sane():
    """Regression guard: prevent the quarterly-total-as-daily-average bug that
    produced ~10,000% utilization readings. All nine gates must sit in their
    natural ranges; if any explodes, the Phase-1 bridge or demand/capacity math
    has regressed on unit handling."""

    response = client.get("/api/v1/viability/baseline", headers={"X-Role": "analyst"})
    assert response.status_code == 200
    conditions = {c["metric"]: c for c in response.json()["data"]["report"]["conditions"]}

    # Gate 1: vehicle utilization is a ratio; any value above 5x (500%) means
    # demand has been inflated by the whole-quarter-as-a-day bug.
    g1 = conditions[1]["actual"]
    assert 0.0 <= g1 <= 5.0, f"Vehicle utilization should be a ratio, got {g1}"

    # Gate 2: billed utilization should track vehicle utilization within a
    # small no-show correction window; values 10x+ indicate dimensional bugs.
    g2 = conditions[2]["actual"]
    assert 0.0 <= g2 <= 5.0, f"Billed utilization should be a ratio, got {g2}"

    # Gate 3: total volume pool lives in [0, 3] in practice (overbooking ~1.2).
    g3 = conditions[3]["actual"]
    assert 0.0 <= g3 <= 3.0, f"Total volume pool out of band, got {g3}"

    # Gate 4: revenue per Kent-Leg is a dollar amount; $0 - $300 is sane.
    g4 = conditions[4]["actual"]
    assert 0.0 <= g4 <= 300.0, f"Revenue/KL out of band, got {g4}"

    # Gate 5: high-acuity mix is a proportion.
    g5 = conditions[5]["actual"]
    assert 0.0 <= g5 <= 1.0, f"High-acuity mix must be a proportion, got {g5}"

    # Gate 6: non-billable no-show rate is a proportion.
    g6 = conditions[6]["actual"]
    assert 0.0 <= g6 <= 1.0, f"Non-billable no-show must be a proportion, got {g6}"

    # Gate 7: road hours per vehicle per day - 0-12 hr realistic envelope.
    g7 = conditions[7]["actual"]
    assert 0.0 <= g7 <= 12.0, f"Road hours out of band, got {g7}"

    # Gate 8: contract concentration is a proportion.
    g8 = conditions[8]["actual"]
    assert 0.0 <= g8 <= 1.0, f"Concentration must be a proportion, got {g8}"

    # Gate 9: cost per road hour in dollars (realistic ceiling ~$500 even for
    # pathological fleets); zero is possible when road-hours fall to zero.
    g9 = conditions[9]["actual"]
    assert 0.0 <= g9 <= 500.0, f"Cost/road-hour out of band, got {g9}"


def test_phase1_bridge_produces_daily_averages_not_quarterly_totals(tmp_path):
    """Regression: phase1_bridge must divide quarterly contract rows by the
    number of distinct service days so VariableMapper's `daily_rides` field
    is truly a daily average. This guards the root-cause of the 10,000%+
    utilization bug."""

    from engine.input_layer.phase1_bridge import phase1_csv_dir_to_raw_ingest
    from engine.input_layer.variable_mapping import VariableMapper
    from engine.input_layer.normalization import MetricsNormalizer
    from scripts.build_phase1_canonical_base import (  # type: ignore[import-not-found]
        run_phase1_extract,
        validate_phase1_workbooks,
    )

    inputs = repo_root() / "code" / "inputs"
    q1 = inputs / "Q1 Daily Metrics 2026.xlsx"
    template = inputs / "RideYourWay_Prospective_Market_Intake_Template.xlsx"
    example = inputs / "RideYourWay_Prospective_Market_Intake_Example.xlsx"
    if not q1.is_file():
        # Container/test environment doesn't bundle the reference workbook;
        # skip rather than fail.
        import pytest as _pytest

        _pytest.skip(f"Missing bundled workbook: {q1}")

    phase1_dir = tmp_path / "phase1"
    validate_phase1_workbooks(q1, template, example)
    run_phase1_extract(q1, phase1_dir, template, example)
    raw = phase1_csv_dir_to_raw_ingest(phase1_dir)

    tp = raw["total_performance"]
    assert len(tp) == 1
    row = tp[0]
    assert row.get("service_days", 0) > 1, (
        "Bridge must record the unique service-day count; without it the "
        "downstream 'daily_rides' field becomes a quarterly total."
    )
    assert row["total_rides"] < 2000, (
        "Daily ride average should be at most low-thousands; got "
        f"{row['total_rides']} which suggests quarterly totals are leaking "
        "through as daily numbers."
    )

    normalized = MetricsNormalizer().normalize(raw)
    mapped = VariableMapper().map(normalized)
    assert mapped["baselines"]["daily_rides"] < 2000
    # Road hours baseline is now surfaced from the Vehicle Breakdown sheet.
    assert mapped["baselines"]["road_hours_per_vehicle_per_day"] > 0


def test_intake_upload_runs_example_workbook_end_to_end():
    assert INTAKE_EXAMPLE_PATH.is_file(), f"Missing bundled example: {INTAKE_EXAMPLE_PATH}"
    content = INTAKE_EXAMPLE_PATH.read_bytes()
    files = {
        "file": (
            INTAKE_EXAMPLE_PATH.name,
            content,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    }
    response = client.post(
        "/api/v1/jobs/intake-upload", files=files, headers={"X-Role": "analyst"}
    )
    assert response.status_code == 200
    job_id = response.json()["data"]["job_id"]
    body = _poll_job(job_id, timeout_seconds=120.0)
    assert body["status"] == "completed", body
    result = body["result"]
    assert result is not None
    viability = result["viability"]
    assert viability["readiness_state"] in {"Ready", "Not Ready", "Insufficient Data"}
    intake = result["intake"]
    assert intake["organization"].get("organization_name")
    contracts = intake["prospective_contracts"]
    assert len(contracts) > 0
    assert all(c["estimated_daily_rides"] > 0 for c in contracts)
    assert {c["order_modes"][0] for c in contracts} <= {
        "ambulatory",
        "wheelchair",
        "stretcher",
        "securecare",
    }


def test_list_dispatches_and_payments():
    r1 = client.get("/api/v1/dispatches", headers={"X-Role": "analyst"})
    assert r1.status_code == 200
    assert r1.json()["data"]["items"] == []
    r2 = client.get("/api/v1/payments", headers={"X-Role": "analyst"})
    assert r2.status_code == 200
    assert r2.json()["data"]["items"] == []


def test_rbac_enforced_on_booking_create():
    payload = {"rider_name": "User", "pickup": "A", "dropoff": "B", "mode": "ambulatory"}
    forbidden = client.post("/api/v1/bookings", json=payload, headers={"X-Role": "analyst"})
    assert forbidden.status_code == 403

    allowed = client.post("/api/v1/bookings", json=payload, headers={"X-Role": "ops"})
    assert allowed.status_code == 200
