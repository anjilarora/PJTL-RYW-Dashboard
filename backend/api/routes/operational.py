"""Dashboard endpoints that expose the Operational Deep Dive aggregates.

Each endpoint wraps a pure loader from
``code/backend/engine/operational_service.py``. Loaders read CSVs written by
``code/inference_engine/scripts/operational_eda.py``; the notebook
``code/inference_engine/notebooks/operational_eda.ipynb`` is the human-
readable driver.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status

from api.auth import get_role, require_role
from api.limiter import limiter
from api.schemas import ApiResponse, Role
from engine import operational_service as ops


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/dashboard", tags=["operational"])


def _safe(loader):
    try:
        return loader()
    except ops.OperationalDataMissing as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"reason": "operational_eda_artifact_missing", "message": str(exc)},
        )


@router.get("/fleet-scorecard", response_model=ApiResponse)
@limiter.limit("120/minute")
def d1_fleet_scorecard(request: Request, role: Role = Depends(get_role)) -> ApiResponse:
    require_role("analyst", role)
    return ApiResponse(data=_safe(ops.fleet_scorecard))


@router.get("/weekly-trend", response_model=ApiResponse)
@limiter.limit("120/minute")
def d2_weekly_trend(request: Request, role: Role = Depends(get_role)) -> ApiResponse:
    require_role("analyst", role)
    return ApiResponse(data=_safe(ops.weekly_trend))


@router.get("/mode-profitability", response_model=ApiResponse)
@limiter.limit("120/minute")
def d3_mode_profitability(request: Request, role: Role = Depends(get_role)) -> ApiResponse:
    require_role("analyst", role)
    return ApiResponse(data=_safe(ops.mode_profitability))


@router.get("/otp", response_model=ApiResponse)
@limiter.limit("120/minute")
def d4_otp(request: Request, role: Role = Depends(get_role)) -> ApiResponse:
    require_role("analyst", role)
    return ApiResponse(data=_safe(ops.otp_matrix))


@router.get("/payer-concentration", response_model=ApiResponse)
@limiter.limit("120/minute")
def d5_payer_concentration(request: Request, role: Role = Depends(get_role)) -> ApiResponse:
    require_role("analyst", role)
    return ApiResponse(data=_safe(ops.payer_concentration))


@router.get("/hourly-demand", response_model=ApiResponse)
@limiter.limit("120/minute")
def d6_hourly_demand(request: Request, role: Role = Depends(get_role)) -> ApiResponse:
    require_role("analyst", role)
    return ApiResponse(data=_safe(ops.hourly_demand))


@router.get("/cancellations", response_model=ApiResponse)
@limiter.limit("120/minute")
def d7_cancellations(request: Request, role: Role = Depends(get_role)) -> ApiResponse:
    require_role("analyst", role)
    return ApiResponse(data=_safe(ops.cancellations))


@router.get("/rev-per-kl", response_model=ApiResponse)
@limiter.limit("120/minute")
def d8_rev_per_kl(request: Request, role: Role = Depends(get_role)) -> ApiResponse:
    require_role("analyst", role)
    return ApiResponse(data=_safe(ops.rev_per_kentleg))


@router.get("/securecare-compare", response_model=ApiResponse)
@limiter.limit("120/minute")
def d9_securecare_compare(request: Request, role: Role = Depends(get_role)) -> ApiResponse:
    require_role("analyst", role)
    return ApiResponse(data=_safe(ops.securecare_compare))


@router.get("/cost-regional", response_model=ApiResponse)
@limiter.limit("120/minute")
def d10_cost_regional(request: Request, role: Role = Depends(get_role)) -> ApiResponse:
    require_role("analyst", role)
    return ApiResponse(data=_safe(ops.regional_cost))
