from __future__ import annotations

import logging
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Request, UploadFile, status

from api.auth import get_role, require_role
from api.jobs_store import job_store
from api.limiter import limiter
from api.repo_root import repo_root
from api.schemas import ApiResponse, Role
from api.upload_pipeline import (
    MAX_UPLOAD_BYTES,
    cleanup_work_dir,
    prepare_work_dir,
    run_upload_job,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])


def _content_looks_like_ooxml_zip(content: bytes) -> bool:
    """True if bytes start with a ZIP local file header (OOXML .xlsx is ZIP-based)."""
    if len(content) < 4:
        return False
    return content[0:2] == b"PK" and content[2] == 0x03 and content[3] == 0x04


def _run_job_safe(job_id: str, work_dir: Path, q1_file: Path) -> None:
    try:
        run_upload_job(job_id, q1_file, work_dir)
    finally:
        cleanup_work_dir(work_dir)


@router.post("/upload", response_model=ApiResponse)
@limiter.limit("10/minute")
async def upload_workbook(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    role: Role = Depends(get_role),
) -> ApiResponse:
    require_role("analyst", role)
    name = (file.filename or "upload.xlsx").lower()
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
    if not _content_looks_like_ooxml_zip(content):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "File is not a valid ZIP-based Excel workbook (.xlsx)"},
        )

    try:
        repo_root()
    except FileNotFoundError as exc:
        logger.error("Repo root not found for upload pipeline: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Server configuration error: repository layout not found"},
        ) from exc

    work_dir = prepare_work_dir()
    q1_path = work_dir / "Q1_upload.xlsx"
    q1_path.write_bytes(content)
    job_id = job_store.create()
    background_tasks.add_task(_run_job_safe, job_id, work_dir, q1_path)
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
