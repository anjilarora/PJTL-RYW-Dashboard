from __future__ import annotations

import logging

from fastapi import Depends, Header, HTTPException, Request, status

from api.config import Settings, get_settings
from api.schemas import Role

logger = logging.getLogger(__name__)

ROLE_ORDER = {"analyst": 1, "ops": 2, "admin": 3}


def _role_from_header(x_role: str | None) -> Role:
    role = (x_role or "analyst").strip().lower()
    if role not in ROLE_ORDER:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Unsupported role '{role}'. Use analyst, ops, or admin.",
        )
    return role  # type: ignore[return-value]


def _role_from_jwt(authorization: str | None, settings: Settings) -> Role:
    if not settings.jwt_secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="JWT auth configured but RYW_JWT_SECRET is not set",
        )
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization: Bearer <token> required",
        )
    token = authorization.split(" ", 1)[1].strip()
    try:
        import jwt
    except ImportError as exc:  # pragma: no cover
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="PyJWT is required for RYW_AUTH_MODE=jwt",
        ) from exc
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
    except Exception as exc:
        logger.debug("JWT decode failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from exc
    raw = str(payload.get(settings.jwt_role_claim, "analyst")).strip().lower()
    if raw not in ROLE_ORDER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Token role '{raw}' is not allowed",
        )
    return raw  # type: ignore[return-value]


def get_role(
    _request: Request,
    settings: Settings = Depends(get_settings),
    authorization: str | None = Header(default=None, alias="Authorization"),
    x_role: str | None = Header(default=None, alias="X-Role"),
) -> Role:
    if settings.auth_mode == "jwt":
        return _role_from_jwt(authorization, settings)
    return _role_from_header(x_role)


def require_role(minimum: Role, actual: Role) -> None:
    if ROLE_ORDER[actual] < ROLE_ORDER[minimum]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role '{actual}' cannot perform this operation. Requires '{minimum}' or above.",
        )
