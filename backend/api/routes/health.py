from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from api.schemas import ApiResponse
from inference.service import engine

router = APIRouter(tags=["health"])


@router.get("/health", response_model=ApiResponse)
def health() -> ApiResponse:
    return ApiResponse(data={"status": "ok", "inference": engine.health_snapshot()})


@router.get("/ready", response_model=ApiResponse)
def ready() -> ApiResponse:
    snap = engine.health_snapshot()
    if not snap.get("model_loaded"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "reason": "inference_model_not_ready",
                "load_error": snap.get("load_error"),
                "model_dir": snap.get("model_dir"),
            },
        )
    return ApiResponse(data={"status": "ready", "inference": snap})
