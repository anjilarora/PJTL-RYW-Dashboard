#!/usr/bin/env python3
"""Build readiness training base CSV from generated training rows + shared KPI config."""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_CODE = Path(__file__).resolve().parents[1]
if str(_CODE) not in sys.path:
    sys.path.insert(0, str(_CODE))
from lib.repo_paths import code_root_from_anchor

CODE_ROOT = code_root_from_anchor(Path(__file__).parent)
ROWS_IN = CODE_ROOT / "intermediates" / "training" / "readiness_training_rows.csv"
PHASE1 = CODE_ROOT / "intermediates" / "phase1"
OUT_CSV = PHASE1 / "readiness_training_base.csv"
OUT_PROV = PHASE1 / "readiness_training_provenance.json"
KPI_DOC = CODE_ROOT / "config" / "pjtl_kpis_and_formulas.json"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _passes(value: float, threshold: float, pass_rule: str) -> bool:
    if pass_rule == "gte":
        return value >= threshold
    if pass_rule == "lte":
        return value <= threshold
    if pass_rule == "lt":
        return value < threshold
    if pass_rule == "gt":
        return value > threshold
    raise ValueError(f"Unknown pass_rule: {pass_rule}")


def main() -> None:
    if not KPI_DOC.is_file():
        raise SystemExit(f"Missing KPI config: {KPI_DOC}")
    if not ROWS_IN.is_file():
        raise SystemExit(f"Missing training row export: {ROWS_IN}")

    doc = json.loads(KPI_DOC.read_text(encoding="utf-8"))
    metrics = sorted(doc["readiness_metrics"], key=lambda x: int(x["metric_number"]))
    order = [m["key"] for m in metrics]
    rules = {m["key"]: (float(m["threshold"]), m["pass_rule"]) for m in metrics}

    input_hash = _sha256(ROWS_IN)

    with ROWS_IN.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        missing = [c for c in order if c not in (reader.fieldnames or [])]
        if missing:
            raise SystemExit(f"readiness_training_rows.csv missing columns: {missing}")
        rows_in = list(reader)

    out_rows: list[dict[str, object]] = []
    ref_disagree = 0
    ref_total = 0
    for row in rows_in:
        feats = {k: float(row[k]) for k in order}
        passes = all(
            _passes(feats[k], rules[k][0], rules[k][1]) for k in order
        )
        label = 1 if passes else 0
        if "label_ready_reference" in row and row["label_ready_reference"] not in ("", None):
            ref_total += 1
            if int(float(row["label_ready_reference"])) != label:
                ref_disagree += 1
        out_row = {**{k: feats[k] for k in order}, "label_ready": label}
        out_rows.append(out_row)

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = order + ["label_ready"]
    with OUT_CSV.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(out_rows)

    if ref_total:
        rate = ref_disagree / ref_total
        print(f"Gate-derived label vs label_ready_reference: {ref_disagree}/{ref_total} disagree ({rate:.1%})")

    prov = {
        "artifact_filename": "readiness_training_base.csv",
        "generator_script": "code/scripts/build_readiness_training_base.py",
        "input_rows_file": str(ROWS_IN.relative_to(CODE_ROOT.parent)),
        "input_rows_sha256": input_hash,
        "kpi_config": str(KPI_DOC.relative_to(CODE_ROOT.parent)),
        "schema_version": doc.get("schema_version"),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "row_count": len(out_rows),
        "label_ready_definition": "all_nine_gates_pass_per_pjtl_kpis_and_formulas_json",
        "reference_disagreement": {"count": ref_disagree, "compared": ref_total} if ref_total else None,
    }
    OUT_PROV.write_text(json.dumps(prov, indent=2), encoding="utf-8")
    print(f"Wrote {OUT_CSV} ({len(out_rows)} rows)")
    print(f"Wrote {OUT_PROV}")


if __name__ == "__main__":
    main()
