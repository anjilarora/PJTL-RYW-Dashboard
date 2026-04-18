from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from api.auth import get_role, require_role
from api.baseline import get_baseline_viability
from api.limiter import limiter
from api.schemas import ApiResponse, EvaluateRequest, Role
from api.viability_service import evaluate_market

router = APIRouter(prefix="/api/v1/viability", tags=["viability"])


@router.post("/evaluate", response_model=ApiResponse)
@limiter.limit("60/minute")
def evaluate(
    request: Request,
    payload: EvaluateRequest,
    role: Role = Depends(get_role),
) -> ApiResponse:
    require_role("analyst", role)
    result = evaluate_market(
        market_profile_input=payload.market_profile.model_dump(),
        historical_data=payload.historical_data,
        external_data=payload.external_data,
        scenario_overrides=payload.scenario_overrides,
    )
    return ApiResponse(data=result)


@router.get("/baseline", response_model=ApiResponse)
@limiter.limit("60/minute")
def baseline(
    request: Request,
    role: Role = Depends(get_role),
) -> ApiResponse:
    """Return the frozen Q1 Daily Metrics viability payload (computed once, cached)."""

    require_role("analyst", role)
    return ApiResponse(data=get_baseline_viability())
