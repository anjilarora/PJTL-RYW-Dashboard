#!/usr/bin/env python3
"""Write FastAPI OpenAPI schema to code/backend/openapi.generated.json (run from dev env with backend installed)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

_BACKEND = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(_BACKEND))

from api.app import app  # noqa: E402

OUT = _BACKEND / "openapi.generated.json"


def main() -> None:
    OUT.write_text(json.dumps(app.openapi(), indent=2), encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
