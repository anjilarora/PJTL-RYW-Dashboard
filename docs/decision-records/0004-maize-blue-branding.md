# ADR 0004 - Michigan maize-blue branding

## Status

Accepted (2026-04-15).

## Context

The Ride YourWay readiness dashboard is the tangible deliverable of the
PJTL x Ride YourWay project track at the University of Michigan. Earlier
iterations used a generic dark UI (black background, teal accent). User
feedback was clear: the product did not visually tie into PJTL or
Michigan, and the generic palette produced poor contrast for the
pass/fail pills.

## Decision

Adopt the Michigan maize-blue palette as the primary brand surface:

- `--navy = #00274c` (Michigan blue) - page hero, sidebar, card
  borders.
- `--maize = #ffcb05` (Michigan maize) - highlights, focus rings,
  call-to-action accents.
- `--maize-soft` and `--maize-ink` for legible maize-on-ink
  compositions.

Status colors remain green / amber / red so that maize never gets
confused with a status signal.

Concrete artifacts:

- [RywLogo.vue](../../frontend/components/RywLogo.vue) renders the
  provided RYW glyph across the topbar and landing hero.
- [layouts/default.vue](../../frontend/layouts/default.vue) sets the
  navy background and maize accent strip on the topbar.
- [MarketHero.vue](../../frontend/components/MarketHero.vue) carries
  the maize highlight behind the market name.

## Consequences

- The UI is visually recognizable as a PJTL x Ride YourWay product.
- The pass/fail/provisional pills remain readable because they live in
  their own green/amber/red token space.
- A `--amber-ink` token is required so provisional text remains legible
  on the amber pill. This token must appear in both `:root` and
  `html[data-theme="light"]` to survive the light-mode override
  pattern.

## Alternatives considered

- **Dark generic with PJTL logo.** Rejected for insufficient
  brand tie-in.
- **Maize-dominant palette.** Rejected; too much maize created an
  unpleasant glare on large panels.
- **Separate "dashboard" vs "marketing" themes.** Overkill; one
  shared theme tokenized through `main.css` is enough.
