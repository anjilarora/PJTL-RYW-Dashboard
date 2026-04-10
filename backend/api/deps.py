"""Shared FastAPI dependencies."""

from __future__ import annotations

from api.auth import get_role
from api.config import Settings, get_settings

__all__ = ["get_role", "get_settings", "Settings"]
