from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from api.auth import get_role, require_role
from api.limiter import limiter
from api.metrics import snapshot
from api.schemas import ApiResponse, Role

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


@router.get("/metrics", response_model=ApiResponse)
@limiter.limit("30/minute")
def get_metrics(
    request: Request,
    role: Role = Depends(get_role),
) -> ApiResponse:
    require_role("admin", role)
    return ApiResponse(data=snapshot())
