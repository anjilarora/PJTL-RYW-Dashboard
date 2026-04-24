# Intermediates (lean snapshot)

Generated CSV/JSON derivations between `code/inputs/*.xlsx` and `code/outputs/`.
This directory was intentionally slimmed down during cleanup.

| Path | Contents |
| --- | --- |
| `inference_inputs/` | Minimal snapshot metadata (`MANIFEST.json`, `MANIFEST.upstream.json`) plus README. |

`phase1/` and `training/` artifacts were removed and can be regenerated from
the build scripts in `code/scripts/` when needed.

Folder contract: `code/inputs/` = `.xlsx`, `code/intermediates/` = CSV/JSON,
`code/outputs/` = model artifacts + selected reports.
