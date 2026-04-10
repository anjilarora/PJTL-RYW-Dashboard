"""Run Phase-1 extract + engine bridge + viability evaluation for upload jobs."""

from __future__ import annotations

import json
import logging
import shutil
import sys
import tempfile
import time
from pathlib import Path

from api.jobs_store import job_store
from api.repo_root import repo_root
from api.viability_service import evaluate_market
from engine.input_layer.phase1_bridge import phase1_csv_dir_to_historical_data

logger = logging.getLogger(__name__)

MAX_UPLOAD_BYTES = 50 * 1024 * 1024


DEFAULT_MARKET_PROFILE: dict = {
    "region": {"region_name": "Grand Rapids North Corridor", "state": "MI"},
    "fleet": {
        "wheelchair_vehicles": 2,
        "ambulatory_vehicles": 2,
        "stretcher_vehicles": 1,
        "securecare_vehicles": 1,
        "drivers": 8,
    },
    "prospective_contracts": [],
}


def _ensure_scripts_importable() -> Path:
    root = repo_root()
    code_dir = root / "code"
    if str(code_dir) not in sys.path:
        sys.path.insert(0, str(code_dir))
    return root


def _default_intake_workbooks(repo_root: Path) -> tuple[Path, Path]:
    inputs_dir = repo_root / "code" / "inputs"
    return (
        inputs_dir / "RideYourWay_Prospective_Market_Intake_Template.xlsx",
        inputs_dir / "RideYourWay_Prospective_Market_Intake_Example.xlsx",
    )


def run_upload_job(job_id: str, q1_path: Path, work_dir: Path) -> None:
    repo_root = _ensure_scripts_importable()
    template_path, example_path = _default_intake_workbooks(repo_root)
    job_t0 = time.perf_counter()

    def step(step_id: str, label: str, status: str, detail: str | None = None) -> None:
        job_store.update_step(job_id, step_id, label, status, detail)

    def log_event(event: str, **fields: object) -> None:
        payload = {"event": event, "job_id": job_id, **fields}
        logger.info(json.dumps(payload, default=str))

    try:
        step("received", "Received upload", "completed", str(q1_path.name))
        log_event("upload_job_received", q1_file=str(q1_path.name))
        if not template_path.is_file() or not example_path.is_file():
            raise FileNotFoundError(
                f"Repo intake workbooks missing (expected {template_path} and {example_path})"
            )

        from scripts.build_phase1_canonical_base import (  # noqa: E402
            run_phase1_extract,
            validate_phase1_workbooks,
        )

        step("validate", "Validating workbook sheets", "running")
        t0 = time.perf_counter()
        validate_phase1_workbooks(q1_path, template_path, example_path)
        log_event("upload_job_validate_ok", duration_ms=round((time.perf_counter() - t0) * 1000, 2))
        step("validate", "Validating workbook sheets", "completed")

        phase1_out = work_dir / "phase1"
        step("phase1", "Phase-1 extraction (canonical CSVs)", "running")
        t0 = time.perf_counter()
        summary = run_phase1_extract(q1_path, phase1_out, template_path, example_path)
        counts = summary.get("table_row_counts", {})
        log_event(
            "upload_job_phase1_ok",
            duration_ms=round((time.perf_counter() - t0) * 1000, 2),
            table_count=len(counts),
        )
        step(
            "phase1",
            "Phase-1 extraction (canonical CSVs)",
            "completed",
            f"tables: {len(counts)}",
        )

        step("normalize", "Normalize & map to engine inputs", "running")
        t0 = time.perf_counter()
        historical_data = phase1_csv_dir_to_historical_data(phase1_out)
        log_event("upload_job_normalize_ok", duration_ms=round((time.perf_counter() - t0) * 1000, 2))
        step("normalize", "Normalize & map to engine inputs", "completed")

        step("pipeline", "Viability pipeline + ML inference", "running")
        t0 = time.perf_counter()
        viability_payload = evaluate_market(
            market_profile_input=DEFAULT_MARKET_PROFILE,
            historical_data=historical_data,
            external_data=None,
            scenario_overrides=None,
        )
        log_event("upload_job_pipeline_ok", duration_ms=round((time.perf_counter() - t0) * 1000, 2))
        step("pipeline", "Viability pipeline + ML inference", "completed")

        result = {
            "viability": viability_payload,
            "phase1_summary": summary,
            "historical_data_keys": list(historical_data.keys()),
        }
        log_event(
            "upload_job_complete",
            total_duration_ms=round((time.perf_counter() - job_t0) * 1000, 2),
        )
        job_store.complete(job_id, result)
    except Exception as exc:
        logger.exception("Upload job %s failed", job_id)
        log_event(
            "upload_job_failed",
            error=str(exc),
            total_duration_ms=round((time.perf_counter() - job_t0) * 1000, 2),
        )
        step("error", "Job failed", "failed", str(exc))
        job_store.fail(job_id, str(exc))


def prepare_work_dir() -> Path:
    return Path(tempfile.mkdtemp(prefix="ryw-upload-"))


def cleanup_work_dir(work_dir: Path) -> None:
    shutil.rmtree(work_dir, ignore_errors=True)
