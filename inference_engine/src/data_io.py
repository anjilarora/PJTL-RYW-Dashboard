from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


def engine_root() -> Path:
    return Path(__file__).resolve().parents[1]


def inputs_dir() -> Path:
    return engine_root() / "inputs"


def load_manifest() -> dict[str, Any]:
    path = inputs_dir() / "MANIFEST.json"
    if not path.exists():
        raise FileNotFoundError(f"Missing {path}; run scripts/sync_inputs_from_phase1.py")
    return json.loads(path.read_text(encoding="utf-8"))


def verify_manifest_files() -> list[str]:
    """Return list of missing input filenames (empty if OK)."""
    manifest = load_manifest()
    missing: list[str] = []
    for entry in manifest.get("files", []):
        name = entry.get("filename")
        if not name:
            continue
        p = inputs_dir() / name
        if not p.exists():
            missing.append(name)
    return missing


def load_csv(name: str, **kwargs: Any) -> pd.DataFrame:
    path = inputs_dir() / name
    if not path.exists():
        raise FileNotFoundError(path)
    return pd.read_csv(path, **kwargs)


def missingness_report(df: pd.DataFrame, name: str = "frame") -> pd.DataFrame:
    counts = df.isna().sum()
    pct = (counts / max(len(df), 1)).round(4)
    out = pd.DataFrame({"column": counts.index, "missing_n": counts.values, "missing_pct": pct.values})
    out.insert(0, "table", name)
    return out.sort_values("missing_n", ascending=False)
