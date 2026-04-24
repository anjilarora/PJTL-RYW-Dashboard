#!/usr/bin/env python3
"""Copy code/intermediates (regenerable phase artifacts pruned) artifacts into code/intermediates/inference_inputs and write MANIFEST.json + MANIFEST.upstream.json."""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

_CODE = Path(__file__).resolve().parents[2]
if str(_CODE) not in sys.path:
    sys.path.insert(0, str(_CODE))
from lib.repo_paths import code_root_from_anchor, repo_root_from_anchor

REPO_ROOT = repo_root_from_anchor(Path(__file__).parent)
CODE_ROOT = code_root_from_anchor(Path(__file__).parent)
PHASE1 = CODE_ROOT / "intermediates" / "phase1"
INPUTS = CODE_ROOT / "intermediates" / "inference_inputs"

GLOBS = [
    "*_base.csv",
    "missingness_audit.csv",
    "field_dictionary.csv",
    "join_key_inventory.csv",
    "minimum_viable_subset.csv",
    "quarantine_list.csv",
    "sheet_lineage_map.csv",
    "unit_dictionary.csv",
]

# Optional audit files in phase1 (not matched by globs above)
EXTRA_PHASE1_FILES = [
    "readiness_training_provenance.json",
]

# Workbooks that build_phase1_canonical_base.py reads (repo-relative to REPO_ROOT)
_UP = "code/inputs"
UPSTREAM_WORKBOOKS: list[tuple[str, str]] = [
    (f"{_UP}/Q1 Daily Metrics 2026.xlsx", "historical_daily_metrics"),
    (f"{_UP}/RideYourWay_Prospective_Market_Intake_Template.xlsx", "prospective_intake_template"),
    (f"{_UP}/RideYourWay_Prospective_Market_Intake_Example.xlsx", "prospective_intake_example"),
]


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _write_upstream_manifest() -> Path:
    workbook_entries: list[dict] = []
    for rel, role in UPSTREAM_WORKBOOKS:
        p = REPO_ROOT / rel
        if p.is_file():
            st = p.stat()
            workbook_entries.append(
                {
                    "role": role,
                    "repo_relative_path": rel.replace("\\", "/"),
                    "present": True,
                    "sha256": _sha256(p),
                    "bytes": st.st_size,
                    "mtime_utc": datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat(),
                }
            )
        else:
            workbook_entries.append(
                {
                    "role": role,
                    "repo_relative_path": rel.replace("\\", "/"),
                    "present": False,
                    "sha256": None,
                    "bytes": None,
                    "mtime_utc": None,
                }
            )

    upstream = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "repo_root": str(REPO_ROOT.resolve()),
        "phase1_builder_script": "code/scripts/build_phase1_canonical_base.py",
        "sync_script": "code/inference_engine/scripts/sync_inputs_from_phase1.py",
        "workbooks": workbook_entries,
    }
    out = INPUTS / "MANIFEST.upstream.json"
    out.write_text(json.dumps(upstream, indent=2), encoding="utf-8")
    return out


def main() -> None:
    if not PHASE1.is_dir():
        raise SystemExit(f"Phase1 directory not found: {PHASE1}")

    INPUTS.mkdir(parents=True, exist_ok=True)
    copied: list[dict] = []

    seen: set[Path] = set()
    for pattern in GLOBS:
        for src in sorted(PHASE1.glob(pattern)):
            if not src.is_file() or src in seen:
                continue
            seen.add(src)
            dest = INPUTS / src.name
            shutil.copy2(src, dest)
            try:
                with dest.open("r", encoding="utf-8", errors="replace") as fh:
                    rows = sum(1 for _ in csv.reader(fh)) - 1
                if rows < 0:
                    rows = 0
            except Exception:
                rows = -1
            copied.append(
                {
                    "filename": dest.name,
                    "source_relative": str(src.relative_to(REPO_ROOT)),
                    "sha256": _sha256(dest),
                    "rows": rows,
                    "bytes": dest.stat().st_size,
                }
            )

    for name in EXTRA_PHASE1_FILES:
        src = PHASE1 / name
        if not src.is_file():
            continue
        dest = INPUTS / name
        shutil.copy2(src, dest)
        copied.append(
            {
                "filename": dest.name,
                "source_relative": str(src.relative_to(REPO_ROOT)),
                "sha256": _sha256(dest),
                "rows": -1,
                "bytes": dest.stat().st_size,
            }
        )

    upstream_path = _write_upstream_manifest()

    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "phase1_source": str(PHASE1.resolve()),
        "upstream_workbooks_manifest": "MANIFEST.upstream.json",
        "data_lineage_doc": "knowledge-base/data-lineage-and-run-order.md",
        "files": sorted(copied, key=lambda x: x["filename"]),
    }
    out = INPUTS / "MANIFEST.json"
    out.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Synced {len(copied)} files into {INPUTS}")
    print(f"Wrote {out}")
    print(f"Wrote {upstream_path}")


if __name__ == "__main__":
    main()
