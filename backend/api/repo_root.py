"""Resolve repository root (directory containing ``code/config/pjtl_kpis_and_formulas.json``).

Resolution order:
  1. ``RYW_REPO_ROOT`` env var (container-friendly override).
  2. Walk upward from this file until the KPI marker is found (local dev).
"""

from __future__ import annotations

import os
from pathlib import Path

_KPI_MARKER = Path("code") / "config" / "pjtl_kpis_and_formulas.json"


def repo_root() -> Path:
    override = os.environ.get("RYW_REPO_ROOT")
    if override:
        candidate = Path(override).resolve()
        if (candidate / _KPI_MARKER).is_file():
            return candidate
        raise FileNotFoundError(
            f"RYW_REPO_ROOT={override!r} is set but {_KPI_MARKER} is not present under it"
        )
    start = Path(__file__).resolve()
    for p in [start, *start.parents]:
        if (p / _KPI_MARKER).is_file():
            return p
    raise FileNotFoundError(f"Could not find repo root (missing {_KPI_MARKER})")
