from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from api.auth import get_role, require_role
from api.limiter import limiter
from api.schemas import ApiResponse, Role
from engine.kpi_config import load_kpi_document

router = APIRouter(prefix="/api/v1/kpis", tags=["kpis"])


@router.get("", response_model=ApiResponse)
@limiter.limit("120/minute")
def get_kpis(
    request: Request,
    role: Role = Depends(get_role),
) -> ApiResponse:
    require_role("analyst", role)
    return ApiResponse(data=load_kpi_document())
