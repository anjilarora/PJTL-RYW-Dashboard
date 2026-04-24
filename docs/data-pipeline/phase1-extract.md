# Phase 1 - canonical base extraction

**Script**:
[code/scripts/build_phase1_canonical_base.py](../../scripts/build_phase1_canonical_base.py)

**Purpose**: Flatten the three xlsx workbooks under `code/inputs/` into
machine-readable CSVs plus JSON field dictionaries under
`code/intermediates/phase1/` during generation. In this trimmed repo those
bulk artifacts are intentionally not tracked; only snapshot metadata under
`code/intermediates/inference_inputs/` is kept.

## Inputs

| File | Role |
|---|---|
| `code/inputs/Q1 Daily Metrics 2026.xlsx` | Frozen operational history for Q1 2026. |
| `code/inputs/RideYourWay_Prospective_Market_Intake_Template.xlsx` | Blank analyst template. |
| `code/inputs/RideYourWay_Prospective_Market_Intake_Example.xlsx` | Worked example used in demos and as a feature-order reference. |

## Outputs

Generated under `code/intermediates/phase1/` (regenerable, not tracked in
this trimmed repository):

- `daily_metrics.csv` - tidy long-form daily metrics extracted from the Q1
  workbook.
- `intake_template_shape.csv` - header and type descriptors from the blank
  template.
- `intake_example_rows.csv` - rows from the example workbook that feed
  downstream feature math.
- `field_dictionary.csv` - one row per field, documenting the sheet,
  column, type, and source formula where known.
- `missingness_audit.csv` - counts of nulls per field so the UI can
  highlight gate inputs that are missing.
- `join_key_inventory.csv` - every join key found across the three
  workbooks with its cardinality, used by the training base builder.
- `phase1_summary.json` - top-level summary with row counts, `output_dir`
  (written as `code/intermediates/phase1`), and the input SHA-256 hashes.

## Determinism

- Excel parsing is done with `openpyxl` using explicit sheet names, never
  by index.
- Row order is sorted deterministically by the join keys before writing
  CSVs so `git diff` on the intermediates is meaningful.
- Every output JSON records input SHA-256 hashes so the provenance chain
  is auditable.

## How to run

```bash
cd code
python scripts/build_phase1_canonical_base.py
```

Exit code is 0 on success. A non-zero exit prints the failing sheet or
field.

## Failure modes

| Symptom | Fix |
|---|---|
| `KeyError: 'Daily Metrics'` | The analyst renamed the sheet; restore the canonical name or extend the sheet-name resolution list in the script. |
| `UnicodeDecodeError` on Kent-Leg | A cell carries a non-UTF-8 character from a pasted source; clean the cell or add a unicode-normalize step. |
| Large row-count diff in `daily_metrics.csv` | The Q1 workbook was reshaped; verify the month range (Dec 29 2025 - Jan 31 2026) and sheet filter. |

## Why the output lives under `code/intermediates/phase1/`

Phase-1 output is **not** user-facing. It exists so that:

1. Training rows and the labeled training base have a stable input.
2. Downstream consumers (notebooks, viability service lineage links) can
   point at specific CSVs by name.
3. PR reviews can inspect diffs on the CSVs when a gate formula changes.

See [architecture/folder-contract.md](../architecture/folder-contract.md)
for the rules that govern this directory.
