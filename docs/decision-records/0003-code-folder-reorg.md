# ADR 0003 - `inputs/`, `intermediates/`, `outputs/` under `code/`

## Status

Accepted (2026-04-15).

## Context

The first iteration placed `inputs/`, `intermediates/`, `outputs/` at
the repo root. That looked tidy in `ls` but:

- The git repo lives in `code/`, not at the repo root. Artifacts
  outside `code/` were untracked, so model diffs had no history and PR
  reviewers could not see pipeline regressions.
- The backend Dockerfile has `context: .` (repo root) but only needs
  `code/`. Having data outside `code/` forced the Dockerfile to copy
  two disjoint subtrees.
- Scripts used two different path-resolution idioms
  (`repo_root_from_anchor()` for some files, manual `..`s for others).

## Decision

Relocate the three data folders under `code/`:

```
code/
  inputs/           <- xlsx only
  intermediates/    <- generated csv/json
  outputs/          <- models, reports, plots
```

Add a single helper
[code/lib/repo_paths.py](../../lib/repo_paths.py) `code_root_from_anchor`
that every script uses to resolve paths. Scripts should prefer
`code_root_from_anchor() / "inputs" / ...` over `repo_root / "code" /
"inputs" / ...`.

Guard rails the move depends on:

- Every metadata/report JSON or CSV carries **repo-relative** paths
  (prefix `code/...`), never absolute.
- The Docker image mirrors `code/` as `/workspace/code/` so upload
  pipeline scripts find the same layout.
- `.gitignore` scrubs the old top-level `inputs/`, `intermediates/`,
  `outputs/` so strays do not reappear.

## Consequences

- Pipeline artifacts are visible in git. PRs now show diffs on
  `code/intermediates (regenerable phase artifacts pruned)/*.csv` and `code/outputs/models/*.json`.
- Scripts converge on one root resolution helper.
- Backend Dockerfile is simpler: a single subtree `COPY`.
- Re-runs need a one-time cleanup (the repo-root folders have been
  deleted in the move commit).

## Alternatives considered

- **Keep at repo root.** Rejected for the reasons above.
- **Move the git repo to the repo root.** Would change every
  contributor's clone layout and the `docker-compose.yml` context.
  Considered invasive for small benefit.
