from __future__ import annotations

import logging
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Request, UploadFile, status

from api.auth import get_role, require_role
from api.intake_pipeline import (
    MAX_UPLOAD_BYTES,
    cleanup_work_dir,
    content_looks_like_ooxml_zip,
    prepare_work_dir,
    run_intake_job,
)
from api.jobs_store import job_store
from api.limiter import limiter
from api.repo_root import repo_root
from api.schemas import ApiResponse, Role

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])


def _run_job_safe(job_id: str, work_dir: Path, intake_file: Path) -> None:
    try:
        run_intake_job(job_id, intake_file, work_dir)
    finally:
        cleanup_work_dir(work_dir)


@router.post("/intake-upload", response_model=ApiResponse)
@limiter.limit("10/minute")
async def upload_intake_workbook(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    role: Role = Depends(get_role),
) -> ApiResponse:
    """Accept a Prospective Market Intake ``.xlsx`` and evaluate it asynchronously."""

    require_role("analyst", role)
    name = (file.filename or "intake.xlsx").lower()
    if not name.endswith(".xlsx"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Only .xlsx workbooks are supported"},
        )
    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": f"File too large (max {MAX_UPLOAD_BYTES} bytes)"},
        )
    if not content_looks_like_ooxml_zip(content):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "File is not a valid ZIP-based Excel workbook (.xlsx)"},
        )

    try:
        repo_root()
    except FileNotFoundError as exc:
        logger.error("Repo root not found for intake pipeline: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Server configuration error: repository layout not found"},
        ) from exc

    work_dir = prepare_work_dir()
    intake_path = work_dir / "intake_upload.xlsx"
    intake_path.write_bytes(content)
    job_id = job_store.create()
    background_tasks.add_task(_run_job_safe, job_id, work_dir, intake_path)
    return ApiResponse(data={"job_id": job_id})


@router.get("/{job_id}", response_model=ApiResponse)
@limiter.limit("120/minute")
def get_job(
    request: Request,
    job_id: str,
    role: Role = Depends(get_role),
) -> ApiResponse:
    require_role("analyst", role)
    rec = job_store.get(job_id)
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"message": "Job not found"})
    return ApiResponse(data=rec.to_dict())
