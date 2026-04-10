"""Lightweight in-process request counters (single-worker demo; replace with Prometheus in production)."""

from __future__ import annotations

import threading
from collections import defaultdict

_lock = threading.Lock()
_total = 0
_by_path: dict[str, int] = defaultdict(int)
_by_status: dict[int, int] = defaultdict(int)


def record_request(path: str, status_code: int) -> None:
    with _lock:
        global _total
        _total += 1
        _by_path[path] += 1
        _by_status[status_code] += 1


def snapshot() -> dict:
    with _lock:
        top_paths = sorted(_by_path.items(), key=lambda x: -x[1])[:25]
        return {
            "total_requests": _total,
            "by_status": dict(_by_status),
            "top_paths": [{"path": p, "count": c} for p, c in top_paths],
        }
