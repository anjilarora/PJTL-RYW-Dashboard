"""ASGI entrypoint for uvicorn: `uvicorn api.main:app`."""

from __future__ import annotations

from api.app import app

__all__ = ["app"]
