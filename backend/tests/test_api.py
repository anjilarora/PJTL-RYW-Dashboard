import zipfile
from io import BytesIO

from fastapi.testclient import TestClient

from api.main import app


client = TestClient(app)


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


def test_upload_rejects_non_zip_body():
    files = {
        "file": (
            "fake.xlsx",
            b"this-is-not-a-zip-file",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    }
    response = client.post("/api/v1/jobs/upload", files=files, headers={"X-Role": "analyst"})
    assert response.status_code == 400


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


def test_upload_job_fails_workbook_validation():
    content = _minimal_invalid_q1_xlsx()
    files = {
        "file": (
            "bad.xlsx",
            content,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    }
    response = client.post("/api/v1/jobs/upload", files=files, headers={"X-Role": "analyst"})
    assert response.status_code == 200
    job_id = response.json()["data"]["job_id"]
    detail = client.get(f"/api/v1/jobs/{job_id}", headers={"X-Role": "analyst"})
    assert detail.status_code == 200
    body = detail.json()["data"]
    assert body["status"] == "failed"
    assert body["error"]


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
