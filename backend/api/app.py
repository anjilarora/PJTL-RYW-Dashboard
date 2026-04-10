from __future__ import annotations

import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from api.config import get_settings
from api.limiter import limiter
from api.middleware.internal_secret import InternalSecretMiddleware
from api.middleware.request_context import RequestContextMiddleware
from api.routes import health, inference_routes, kpis, metrics_admin, operations_demo, upload_jobs, viability

logger = logging.getLogger("ryw")


def _configure_logging() -> None:
    settings = get_settings()
    level_name = (settings.log_level or "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(message)s",
        stream=sys.stdout,
        force=True,
    )


@asynccontextmanager
async def _lifespan(app: FastAPI):
    settings = get_settings()
    if settings.env == "production" and settings.auth_mode == "header":
        logger.warning(
            "RYW_ENV=production with RYW_AUTH_MODE=header: any client can set X-Role; "
            "set RYW_AUTH_MODE=jwt for real authentication."
        )
    if settings.env == "production" and not settings.cors_origins.strip():
        logger.warning(
            "RYW_ENV=production with empty RYW_CORS_ORIGINS: using localhost defaults only; "
            "set explicit origins for deployed frontends."
        )
    yield


def create_app() -> FastAPI:
    _configure_logging()
    settings = get_settings()

    app = FastAPI(
        title="Ride YourWay Backend API",
        version="0.1.0",
        lifespan=_lifespan,
        description=(
            "Market viability and ML-assisted readiness. "
            "**Security:** `X-Role` is not authentication unless `RYW_AUTH_MODE=header` for demos only; "
            "use `RYW_AUTH_MODE=jwt` in production. See `docs/adr/0001-auth-strategy.md`."
        ),
    )
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        s = get_settings()
        rid = getattr(request.state, "request_id", None) or "unknown"
        logger.exception("unhandled error request_id=%s path=%s", rid, request.url.path)
        if s.env == "production" and not s.expose_internal_errors:
            body = {
                "success": False,
                "data": {},
                "error": {
                    "code": "internal_error",
                    "message": "An unexpected error occurred.",
                    "details": {"request_id": rid},
                },
            }
        else:
            body = {
                "success": False,
                "data": {},
                "error": {
                    "code": "internal_error",
                    "message": str(exc),
                    "details": {"request_id": rid},
                },
            }
        return JSONResponse(status_code=500, content=body)

    app.add_middleware(SlowAPIMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestContextMiddleware)
    if settings.internal_api_secret:
        app.add_middleware(InternalSecretMiddleware, secret=settings.internal_api_secret)
        logger.info("Internal API secret enforcement enabled")

    app.include_router(health.router)
    app.include_router(viability.router)
    app.include_router(inference_routes.router)
    app.include_router(kpis.router)
    app.include_router(upload_jobs.router)
    app.include_router(metrics_admin.router)
    if settings.enable_operations_demo:
        app.include_router(operations_demo.router)

    return app


app = create_app()
