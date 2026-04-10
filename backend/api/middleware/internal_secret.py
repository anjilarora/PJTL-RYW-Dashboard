from __future__ import annotations

from typing import Callable

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

_PUBLIC_PATHS = frozenset(
    {
        "/health",
        "/ready",
        "/docs",
        "/openapi.json",
        "/redoc",
        "/favicon.ico",
    }
)


class InternalSecretMiddleware(BaseHTTPMiddleware):
    """Optional gate: require X-Internal-Secret when backend is not exposed directly to browsers."""

    def __init__(self, app, secret: str) -> None:
        super().__init__(app)
        self._secret = secret

    async def dispatch(self, request: Request, call_next: Callable):
        path = request.url.path
        if path in _PUBLIC_PATHS or path.startswith("/docs/"):
            return await call_next(request)
        if request.headers.get("X-Internal-Secret") != self._secret:
            return JSONResponse({"detail": "Forbidden"}, status_code=403)
        return await call_next(request)
