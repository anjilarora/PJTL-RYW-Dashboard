from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from api.auth import get_role, require_role
from api.limiter import limiter
from api.schemas import ApiResponse, InferenceRequest, Role
from inference.service import engine

router = APIRouter(prefix="/api/v1/inference", tags=["inference"])


@router.get("/meta", response_model=ApiResponse)
@limiter.limit("120/minute")
def inference_meta(
    request: Request,
    role: Role = Depends(get_role),
) -> ApiResponse:
    require_role("analyst", role)
    return ApiResponse(data=engine.health_snapshot())


@router.post("/predict", response_model=ApiResponse)
@limiter.limit("120/minute")
def predict(
    request: Request,
    payload: InferenceRequest,
    role: Role = Depends(get_role),
) -> ApiResponse:
    require_role("analyst", role)
    if not engine.model_loaded:
        from fastapi import HTTPException, status

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "reason": "inference_model_not_loaded",
                "load_error": engine.load_error,
            },
        )
    result = engine.predict(payload.model_dump())
    return ApiResponse(
        data={
            "prediction": result.prediction,
            "confidence": result.confidence,
            "probability_ready": result.probability_ready,
            "classification_threshold": engine.classification_threshold,
            "top_drivers": result.top_drivers,
            "model_version": result.model_version,
            "model_evidence": result.model_evidence,
        }
    )
