"""Shared repository root resolution for scripts and tooling."""

from __future__ import annotations

import os
from pathlib import Path

_KPI_REL = Path("code") / "config" / "pjtl_kpis_and_formulas.json"


def repo_root_from_anchor(start: Path | None = None) -> Path:
    """Walk parents from `start` (default: cwd) until KPI config exists.

    ``RYW_REPO_ROOT`` (when set and valid) short-circuits the walk so
    containers that stage a synthetic layout can pin the root directly.
    """
    override = os.environ.get("RYW_REPO_ROOT")
    if override:
        candidate = Path(override).resolve()
        if (candidate / _KPI_REL).is_file():
            return candidate
        raise FileNotFoundError(
            f"RYW_REPO_ROOT={override!r} is set but {_KPI_REL} is not present under it"
        )
    here = (start or Path.cwd()).resolve()
    for p in [here, *here.parents]:
        if (p / _KPI_REL).is_file():
            return p
    raise FileNotFoundError(f"Could not find repo root (missing {_KPI_REL})")


def repo_root_from_file(__file__: str) -> Path:
    """Typical: repo_root_from_file(__file__) from code/scripts/*.py (parents[2])."""
    return Path(__file__).resolve().parents[2]


def code_root_from_anchor(start: Path | None = None) -> Path:
    """Return the ``code/`` directory, the data-contract root.

    All data folders (``inputs/``, ``intermediates/``, ``outputs/``) live under
    ``code/`` so the project stays self-contained. Scripts should use this
    helper rather than hard-coding ``repo_root / "code" / ...``.
    """
    return repo_root_from_anchor(start) / "code"
