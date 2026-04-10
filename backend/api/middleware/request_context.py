from __future__ import annotations

import json
import logging
import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from api.metrics import record_request

logger = logging.getLogger("ryw.api")


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()[:64]
    if request.client:
        return request.client.host or ""
    return ""


def _user_agent(request: Request) -> str:
    ua = request.headers.get("user-agent") or ""
    return ua[:200]


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Adds X-Request-ID and structured access logging."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        rid = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = rid
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            duration_ms = (time.perf_counter() - start) * 1000
            logger.exception(
                json.dumps(
                    {
                        "event": "request_error",
                        "request_id": rid,
                        "path": request.url.path,
                        "method": request.method,
                        "client_ip": _client_ip(request),
                        "user_agent": _user_agent(request),
                        "duration_ms": round(duration_ms, 2),
                    }
                )
            )
            raise
        duration_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Request-ID"] = rid
        record_request(request.url.path, response.status_code)
        logger.info(
            json.dumps(
                {
                    "event": "request",
                    "request_id": rid,
                    "path": request.url.path,
                    "method": request.method,
                    "status_code": response.status_code,
                    "duration_ms": round(duration_ms, 2),
                    "client_ip": _client_ip(request),
                    "user_agent": _user_agent(request),
                }
            )
        )
        return response
