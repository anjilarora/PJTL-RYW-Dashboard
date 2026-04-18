"""Q1 Daily Metrics baseline viability service.

Runs the Phase-1 extract + engine-input normalization + `evaluate_market`
pipeline **once** against the bundled ``code/inputs/Q1 Daily Metrics 2026.xlsx``
workbook. The resulting historical-data dict and viability payload are cached
in-process so subsequent reads (dashboard, intake evaluations) do not re-read
the workbook or re-run XGBoost on the same baseline numbers.
"""

from __future__ import annotations

import csv
import logging
import shutil
import sys
import tempfile
import threading
from pathlib import Path
from typing import Any, Dict, List

from api.repo_root import repo_root
from api.viability_service import evaluate_market

logger = logging.getLogger(__name__)


# Default fleet for the Q1 baseline. Must reflect the fleet that actually ran
# in Q1 (Grand Rapids + Lansing + Battle Creek), otherwise vehicle_utilization
# divides the whole region's demand by a toy fleet and the gate inflates.
# Derived from Q1 Vehicle Breakdown distinct-vehicle counts (28 wheelchair,
# 10 ambulatory) plus the 2 dedicated SecureCare vehicles tracked in
# engine.config.FLEET. No stretcher-dedicated vehicles ran in Q1.
DEFAULT_MARKET_PROFILE: Dict[str, Any] = {
    "region": {"region_name": "Grand Rapids Tri-Region Baseline", "state": "MI"},
    "fleet": {
        "wheelchair_vehicles": 28,
        "ambulatory_vehicles": 10,
        "stretcher_vehicles": 0,
        "securecare_vehicles": 2,
        "drivers": 44,
    },
    "prospective_contracts": [],
}


_cache_lock = threading.Lock()
_cached_historical: Dict[str, Any] | None = None
_cached_viability: Dict[str, Any] | None = None


def _ensure_scripts_importable() -> Path:
    root = repo_root()
    code_dir = root / "code"
    if str(code_dir) not in sys.path:
        sys.path.insert(0, str(code_dir))
    return root


def _bundled_workbook_paths() -> tuple[Path, Path, Path]:
    root = _ensure_scripts_importable()
    inputs_dir = root / "code" / "inputs"
    q1 = inputs_dir / "Q1 Daily Metrics 2026.xlsx"
    template = inputs_dir / "RideYourWay_Prospective_Market_Intake_Template.xlsx"
    example = inputs_dir / "RideYourWay_Prospective_Market_Intake_Example.xlsx"
    for p in (q1, template, example):
        if not p.is_file():
            raise FileNotFoundError(f"Bundled baseline workbook missing: {p}")
    return q1, template, example


_SNF_KEYWORDS = (
    "snf",
    "nursing",
    "rehab",
    "rehabilitation",
    "senior care",
    "care center",
    "care community",
    "valley view",
    "cottage",
    "optalis",
    "allendale",
)
_BROKER_KEYWORDS = ("mtm", "saferide", "modivcare", "feonix", "broker")
_VA_KEYWORDS = ("va", "veteran")
_HOSPITAL_KEYWORDS = ("hospital", "health", "corewell", "bronson", "u of m", "umh", "medical center", "spectrum")


def _classify_payer(payer_id: str) -> tuple[str, str]:
    """Map a free-form payer name to a (contract_type, noshow_tier) pair."""

    p = (payer_id or "").strip().lower()
    if any(k in p for k in _VA_KEYWORDS):
        return "va", "snf"
    if any(k in p for k in _BROKER_KEYWORDS):
        return "broker", "broker"
    if any(k in p for k in _SNF_KEYWORDS):
        return "snf", "snf"
    if any(k in p for k in _HOSPITAL_KEYWORDS):
        return "hospital", "snf"
    return "hospital", "snf"


def _build_prospective_contracts_from_payers(
    phase1_dir: Path, service_days: int, top_n: int = 200
) -> List[Dict[str, Any]]:
    """Aggregate the Q1 payer-summary CSV into a prospective-contract list so
    the baseline concentration gate reflects the real Q1 payer distribution
    rather than a synthetic two-contract default."""

    path = phase1_dir / "payer_summary_base.csv"
    if not path.is_file() or service_days <= 0:
        return []
    agg: Dict[str, Dict[str, float]] = {}
    with path.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            payer = (row.get("payer_id") or "").strip()
            if not payer:
                continue
            slot = agg.setdefault(payer, {"orders": 0.0, "rev": 0.0, "kl": 0.0})
            try:
                slot["orders"] += float(row.get("order_count") or 0)
                slot["rev"] += float(row.get("sum_order_price") or 0)
                slot["kl"] += float(row.get("sum_kent_legs") or 0)
            except (TypeError, ValueError):
                continue
    ranked = sorted(agg.items(), key=lambda kv: -kv[1]["rev"])[:top_n]
    contracts: List[Dict[str, Any]] = []
    for payer, stats in ranked:
        if stats["orders"] <= 0 or stats["kl"] <= 0:
            continue
        daily_rides = stats["orders"] / service_days
        rev_per_trip = stats["rev"] / stats["orders"]
        contract_type, noshow_tier = _classify_payer(payer)
        contracts.append(
            {
                "name": payer,
                "contract_type": contract_type,
                "estimated_daily_rides": round(daily_rides, 3),
                "estimated_revenue_per_trip": round(rev_per_trip, 2),
                # Leave order_modes empty so M1 falls back to the observed
                # historical mode mix (Q1 was ~77% wheelchair, 23% ambulatory)
                # rather than hard-coding a 50/50 split on every payer row.
                "order_modes": [],
                "noshow_billing_tier": noshow_tier,
                "payer_name": payer,
            }
        )
    return contracts


def _compute_baseline() -> tuple[Dict[str, Any], Dict[str, Any]]:
    q1_path, template_path, example_path = _bundled_workbook_paths()

    from engine.input_layer.phase1_bridge import phase1_csv_dir_to_historical_data
    from scripts.build_phase1_canonical_base import (  # type: ignore[import-not-found]
        run_phase1_extract,
        validate_phase1_workbooks,
    )

    work_dir = Path(tempfile.mkdtemp(prefix="ryw-baseline-"))
    try:
        validate_phase1_workbooks(q1_path, template_path, example_path)
        phase1_out = work_dir / "phase1"
        run_phase1_extract(q1_path, phase1_out, template_path, example_path)
        historical_data = phase1_csv_dir_to_historical_data(phase1_out)
        service_days = 1
        tp = historical_data.get("baselines") or {}
        try:
            service_days = max(1, int(round(tp.get("service_days", 0) or 1)))
        except (TypeError, ValueError):
            service_days = 1
        # Re-read service_days from the raw total_performance aggregate; the
        # baselines dict doesn't carry it through by default.
        service_days = _service_days_from_phase1(phase1_out) or service_days
        prospective_contracts = _build_prospective_contracts_from_payers(
            phase1_out, service_days=service_days
        )
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)

    profile = dict(DEFAULT_MARKET_PROFILE)
    profile["prospective_contracts"] = prospective_contracts

    viability = evaluate_market(
        market_profile_input=profile,
        historical_data=historical_data,
        external_data=None,
        scenario_overrides=None,
    )
    return historical_data, viability


def _service_days_from_phase1(phase1_dir: Path) -> int:
    """Count distinct service dates in the Q1 contract-volume extract."""

    path = phase1_dir / "contract_volume_base.csv"
    if not path.is_file():
        return 0
    dates: set[str] = set()
    with path.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            d = (row.get("date_of_service_iso") or row.get("date_of_service") or "").strip()
            if d:
                dates.add(d)
    return len(dates)


def _ensure_cached() -> tuple[Dict[str, Any], Dict[str, Any]]:
    global _cached_historical, _cached_viability
    if _cached_historical is not None and _cached_viability is not None:
        return _cached_historical, _cached_viability
    with _cache_lock:
        if _cached_historical is None or _cached_viability is None:
            logger.info("baseline_pipeline_start")
            _cached_historical, _cached_viability = _compute_baseline()
            logger.info(
                "baseline_pipeline_done readiness=%s tier=%s",
                _cached_viability.get("readiness_state"),
                _cached_viability.get("confidence_tier"),
            )
    assert _cached_historical is not None and _cached_viability is not None
    return _cached_historical, _cached_viability


def get_baseline_historical_data() -> Dict[str, Any]:
    """Return the cached Q1 historical-data dict (engine-shaped)."""

    historical, _ = _ensure_cached()
    return historical


def get_baseline_viability() -> Dict[str, Any]:
    """Return the cached Q1 viability payload (gates + readiness + ML)."""

    _, viability = _ensure_cached()
    return viability


def reset_cache() -> None:
    """Test helper: forget the cached baseline so the next call recomputes."""

    global _cached_historical, _cached_viability
    with _cache_lock:
        _cached_historical = None
        _cached_viability = None
