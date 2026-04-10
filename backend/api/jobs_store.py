"""In-memory job store for async upload pipeline (single-worker demo; swap for Redis later)."""

from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class JobRecord:
    job_id: str
    status: str
    steps: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None
    result: dict[str, Any] | None = None
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "status": self.status,
            "steps": list(self.steps),
            "error": self.error,
            "result": self.result,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class JobStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._jobs: dict[str, JobRecord] = {}

    def create(self) -> str:
        jid = str(uuid.uuid4())
        now = _utc_now()
        with self._lock:
            self._jobs[jid] = JobRecord(
                job_id=jid,
                status="pending",
                steps=[],
                created_at=now,
                updated_at=now,
            )
        return jid

    def get(self, job_id: str) -> JobRecord | None:
        with self._lock:
            r = self._jobs.get(job_id)
            return r

    def update_step(
        self,
        job_id: str,
        step_id: str,
        label: str,
        status: str,
        detail: str | None = None,
    ) -> None:
        with self._lock:
            rec = self._jobs.get(job_id)
            if not rec:
                return
            entry = {
                "id": step_id,
                "label": label,
                "status": status,
                "detail": detail,
                "ts": _utc_now(),
            }
            replaced = False
            for i, s in enumerate(rec.steps):
                if s.get("id") == step_id:
                    rec.steps[i] = entry
                    replaced = True
                    break
            if not replaced:
                rec.steps.append(entry)
            rec.status = "running"
            rec.updated_at = _utc_now()

    def complete(self, job_id: str, result: dict[str, Any]) -> None:
        with self._lock:
            rec = self._jobs.get(job_id)
            if not rec:
                return
            rec.status = "completed"
            rec.result = result
            rec.error = None
            rec.updated_at = _utc_now()

    def fail(self, job_id: str, message: str) -> None:
        with self._lock:
            rec = self._jobs.get(job_id)
            if not rec:
                return
            rec.status = "failed"
            rec.error = message
            rec.updated_at = _utc_now()


job_store = JobStore()
