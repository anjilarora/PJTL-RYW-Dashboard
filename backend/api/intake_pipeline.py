"""Process an uploaded Prospective Market Intake workbook end-to-end.

Given a user-supplied ``.xlsx`` matching
``code/inputs/RideYourWay_Prospective_Market_Intake_Example.xlsx`` shape (the
two sheets ``Organization Intake`` and ``Trip Demand Input``), the pipeline:

1. Extracts both sheets using the existing Phase-1 extractors.
2. Maps each Trip Demand row to a :class:`ProspectiveContract`, falling back to
   Organization Intake metadata where per-row values are missing.
3. Builds a :class:`MarketProfile` on top of the shared default scaffold and
   the Q1 historical-data baseline (loaded via :mod:`api.baseline`).
4. Calls :func:`evaluate_market` to produce gates + readiness + ML inference
   and stores the payload in :data:`api.jobs_store.job_store`.
"""

from __future__ import annotations

import json
import logging
import shutil
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

from api.baseline import DEFAULT_MARKET_PROFILE, get_baseline_historical_data
from api.jobs_store import job_store
from api.repo_root import repo_root
from api.viability_service import evaluate_market

logger = logging.getLogger(__name__)

MAX_UPLOAD_BYTES = 50 * 1024 * 1024

REQUIRED_INTAKE_SHEETS = ("Organization Intake", "Trip Demand Input")

_ORG_TYPE_TO_CONTRACT = {
    "hospital": "hospital",
    "snf": "snf",
    "skilled nursing facility": "snf",
    "broker": "broker",
    "va": "va",
    "veterans": "va",
    "securecare": "securecare",
    "behavioral health": "securecare",
}

# Intake "Trip Mode" values map to the four canonical engine modes
# (ORDER_MODES in engine.config). "stretcher alternative" and variants collapse
# to "stretcher" so they line up with fleet.stretcher_vehicles and the mode-mix
# keys the engine's M1/M3/M5 use; otherwise intake stretcher demand would be
# silently dropped by capacity math.
_TRIP_MODE_NORMALIZED = {
    "ambulatory": "ambulatory",
    "wheelchair": "wheelchair",
    "stretcher": "stretcher",
    "stretcher alternative": "stretcher",
    "stretcher alt": "stretcher",
    "securecare": "securecare",
    "secure care": "securecare",
}

_NOSHOW_TIER_BY_CONTRACT = {
    "hospital": "snf",
    "snf": "snf",
    "va": "va",
    "securecare": "snf",
    "broker": "broker",
}

_FALLBACK_PRICE_BY_MODE = {
    "ambulatory": 62.0,
    "wheelchair": 84.0,
    "stretcher": 225.0,
    "securecare": 240.0,
}


def _ensure_scripts_importable() -> Path:
    root = repo_root()
    code_dir = root / "code"
    if str(code_dir) not in sys.path:
        sys.path.insert(0, str(code_dir))
    return root


def prepare_work_dir() -> Path:
    return Path(tempfile.mkdtemp(prefix="ryw-intake-"))


def cleanup_work_dir(work_dir: Path) -> None:
    shutil.rmtree(work_dir, ignore_errors=True)


def _safe_float(value: Any) -> float:
    if value is None or value == "":
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _normalize_mode(raw: str) -> str | None:
    key = (raw or "").strip().lower()
    return _TRIP_MODE_NORMALIZED.get(key)


def _normalize_contract_type(raw: str) -> str:
    key = (raw or "").strip().lower()
    return _ORG_TYPE_TO_CONTRACT.get(key, "snf")


def validate_intake_workbook(path: Path) -> None:
    """Raise ValueError if ``path`` is missing either required intake sheet."""

    _ensure_scripts_importable()
    from scripts.build_phase1_canonical_base import list_xlsx_sheet_names  # type: ignore[import-not-found]

    names = list_xlsx_sheet_names(path)
    missing = [s for s in REQUIRED_INTAKE_SHEETS if s not in names]
    if missing:
        raise ValueError(
            "Intake workbook missing sheets: "
            f"{missing}; found: {sorted(names)}. Reference shape is "
            "code/inputs/RideYourWay_Prospective_Market_Intake_Example.xlsx."
        )


def intake_rows_to_prospective_contracts(
    trip_rows: List[Dict[str, str]],
    org_metadata: Dict[str, str],
) -> List[Dict[str, Any]]:
    """Map raw extracted intake rows to :class:`ProspectiveContract` dicts.

    Each Trip Demand row becomes one contract. Rows without a normalized trip
    mode or with zero weekly rides are skipped so downstream gates are not
    polluted by empty scaffold rows.
    """

    default_payer = org_metadata.get("contract_payer_name") or org_metadata.get(
        "organization_name"
    )
    org_contract_type = _normalize_contract_type(
        org_metadata.get("organization_type", "") or org_metadata.get("payer_type", "")
    )

    price_by_mode = {
        "ambulatory": _safe_float(org_metadata.get("ambulatory_avg_price_per_trip")),
        "wheelchair": _safe_float(org_metadata.get("wheelchair_avg_price_per_trip")),
        "stretcher": _safe_float(
            org_metadata.get("stretcher_alt_avg_price_per_trip")
            or org_metadata.get("stretcher_avg_price_per_trip")
        ),
        "securecare": _safe_float(org_metadata.get("securecare_avg_price_per_trip")),
    }

    contracts: List[Dict[str, Any]] = []
    for row in trip_rows:
        mode = _normalize_mode(row.get("trip_mode", ""))
        if mode is None:
            continue
        weekly = _safe_float(row.get("completed_trips_week"))
        if weekly <= 0:
            continue
        row_contract_type = _normalize_contract_type(
            row.get("source_type", "") or org_metadata.get("organization_type", "")
        ) or org_contract_type
        per_trip = _safe_float(row.get("avg_revenue_completed_trip"))
        if per_trip <= 0:
            per_trip = price_by_mode.get(mode, 0.0) or _FALLBACK_PRICE_BY_MODE[mode]
        name = (row.get("contract_program") or "").strip() or (
            row.get("organization_name") or default_payer or "Prospective Contract"
        )
        contracts.append(
            {
                "name": name,
                "contract_type": row_contract_type,
                "estimated_daily_rides": round(weekly / 7.0, 3),
                "estimated_revenue_per_trip": per_trip,
                "order_modes": [mode],
                "noshow_billing_tier": _NOSHOW_TIER_BY_CONTRACT.get(row_contract_type, "snf"),
                "payer_name": (row.get("organization_name") or default_payer),
            }
        )

    if not contracts:
        raise ValueError(
            "Intake workbook produced no usable contracts. Ensure Trip Demand Input "
            "has rows with a recognized 'Trip Mode' and positive 'Completed Trips / Week'."
        )
    return contracts


def extract_intake_payload(intake_path: Path) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
    _ensure_scripts_importable()
    from scripts.build_phase1_canonical_base import (  # type: ignore[import-not-found]
        WorkbookReader,
        extract_org_intake,
        extract_trip_demand,
        org_metadata_map,
    )

    reader = WorkbookReader(intake_path)
    try:
        trip_rows = extract_trip_demand(reader, "Trip Demand Input", "uploaded")
        org_rows = extract_org_intake(reader, "Organization Intake", "uploaded")
    finally:
        reader.close()
    metadata = org_metadata_map(org_rows)
    contracts = intake_rows_to_prospective_contracts(trip_rows, metadata)
    return contracts, metadata


def run_intake_job(job_id: str, intake_path: Path, work_dir: Path) -> None:
    """Background task: run the full intake → viability pipeline.

    ``work_dir`` is accepted for parity with the previous upload pipeline and
    is left to the caller to clean up.
    """

    del work_dir  # No Phase-1 CSV output is needed; kept for signature parity.
    job_t0 = time.perf_counter()

    def step(step_id: str, label: str, status: str, detail: str | None = None) -> None:
        job_store.update_step(job_id, step_id, label, status, detail)

    def log_event(event: str, **fields: object) -> None:
        logger.info(json.dumps({"event": event, "job_id": job_id, **fields}, default=str))

    try:
        step("received", "Received intake workbook", "completed", intake_path.name)
        log_event("intake_job_received", file=intake_path.name)

        step("validate", "Validating intake sheets", "running")
        t0 = time.perf_counter()
        validate_intake_workbook(intake_path)
        step("validate", "Validating intake sheets", "completed")
        log_event("intake_job_validate_ok", duration_ms=round((time.perf_counter() - t0) * 1000, 2))

        step("extract", "Extracting organization intake & trip demand", "running")
        t0 = time.perf_counter()
        contracts, metadata = extract_intake_payload(intake_path)
        step(
            "extract",
            "Extracting organization intake & trip demand",
            "completed",
            f"{len(contracts)} prospective contracts",
        )
        log_event(
            "intake_job_extract_ok",
            duration_ms=round((time.perf_counter() - t0) * 1000, 2),
            contract_count=len(contracts),
        )

        step("baseline", "Loading Q1 historical baseline", "running")
        t0 = time.perf_counter()
        historical_data = get_baseline_historical_data()
        step("baseline", "Loading Q1 historical baseline", "completed")
        log_event("intake_job_baseline_ok", duration_ms=round((time.perf_counter() - t0) * 1000, 2))

        market_profile = dict(DEFAULT_MARKET_PROFILE)
        market_profile["prospective_contracts"] = contracts

        step("pipeline", "Viability pipeline + ML inference", "running")
        t0 = time.perf_counter()
        viability_payload = evaluate_market(
            market_profile_input=market_profile,
            historical_data=historical_data,
            external_data=None,
            scenario_overrides=None,
        )
        step("pipeline", "Viability pipeline + ML inference", "completed")
        log_event("intake_job_pipeline_ok", duration_ms=round((time.perf_counter() - t0) * 1000, 2))

        result: Dict[str, Any] = {
            "viability": viability_payload,
            "intake": {
                "organization": metadata,
                "prospective_contracts": contracts,
            },
        }
        log_event(
            "intake_job_complete",
            total_duration_ms=round((time.perf_counter() - job_t0) * 1000, 2),
            contract_count=len(contracts),
            readiness=viability_payload.get("readiness_state"),
        )
        job_store.complete(job_id, result)
    except Exception as exc:
        logger.exception("Intake job %s failed", job_id)
        log_event(
            "intake_job_failed",
            error=str(exc),
            total_duration_ms=round((time.perf_counter() - job_t0) * 1000, 2),
        )
        step("error", "Job failed", "failed", str(exc))
        job_store.fail(job_id, str(exc))


def content_looks_like_ooxml_zip(content: bytes) -> bool:
    """True if ``content`` starts with a ZIP local file header (.xlsx is ZIP)."""

    if len(content) < 4:
        return False
    return content[0:2] == b"PK" and content[2] == 0x03 and content[3] == 0x04
