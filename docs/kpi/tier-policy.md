# Tier policy

Every readiness verdict carries a **confidence tier** that tells the
reader how audited the inputs are. The tier is orthogonal to the
pass/fail verdict - a market can be "No-Go / Tier 1" (we are confident
it fails) or "Ready / Tier 2" (it passes, but some inputs are
assumption-backed).

## The three tiers

### Tier 1 - Audited
- Every input gate is computed from an audited source formula.
- No active assumption touches any gate.
- Analysts can forward the verdict to ops/finance without caveats.

### Tier 2 - Assumption-Backed
- At least one of the assumptions in
  [assumption-register.md](./assumption-register.md) is active.
- The verdict is still trustworthy but the analyst should call out
  which gate is driven by an assumption.
- This is the **default tier** for every market today because the
  charter cost ceiling is universally applied.

### Tier 3 - Override
- An analyst has manually forced the verdict (e.g., marked a market
  Ready despite a failing gate because of a board-approved exception).
- Every Tier 3 verdict carries a mandatory note and the analyst
  user id.
- Tier 3 is visible but discouraged; we log it for audit.

## Where the tier is derived

[code/backend/engine/evaluation/confidence.py](../../backend/engine/evaluation/confidence.py)
`derive_confidence_tier()` takes:

- the nine gate pass/fail states,
- the set of active assumptions,
- any analyst override,

and returns one of `Tier 1 - Audited`, `Tier 2 - Assumption-Backed`,
`Tier 3 - Override`.

## Where the UI shows it

- As a small label below the main `StatusPill` on `MarketHero.vue`.
- Behind a circled-i (`InfoTip`) so the reader can click to read the
  full definition without cluttering the hero.

## Pulling a market out of Tier 2

Retire the assumption that is keeping it there. See
[assumption-register.md](./assumption-register.md) "How to retire an
assumption".

## Why tier lives in a circled-i

Earlier iterations had a dedicated "Tier policy" panel that took up a
full row on the dashboard. It repeated content that was already in the
assumption register and made the hero cramped on smaller viewports.
Moving the definition behind a circled-i freed the hero and kept the
information one click away. See the Apr 11 2026 UX polish commit in
[changelog.md](../changelog.md).
