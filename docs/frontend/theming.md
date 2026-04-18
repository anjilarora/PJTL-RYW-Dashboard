# Theming

The frontend uses a CSS-variable-based design system anchored in the
Michigan maize-blue palette. Tokens live in
[code/frontend/assets/css/main.css](../../frontend/assets/css/main.css)
and are consumed by every component via `var(--...)`.

## Palette tokens

| Token | Dark default | Light override | Purpose |
|---|---|---|---|
| `--navy` | `#00274c` | `#00274c` | Michigan blue. Primary surfaces, hero. |
| `--maize` | `#ffcb05` | `#ffcb05` | Michigan maize. Highlights, accents. |
| `--maize-soft` | tint of `--maize` | tint of `--maize` | Backgrounds for subtle maize highlights. |
| `--maize-ink` | dark text on maize | dark text on maize | Body text inside maize highlights. |
| `--amber-ink` | `#6b4a00` | `#6b4a00` | Text color for provisional status pill. |
| `--pass-bg` / `--pass-ink` | green pair | green pair | Pass pill background and ink. |
| `--fail-bg` / `--fail-ink` | red pair | red pair | Fail pill background and ink. |
| `--provisional-bg` | amber-soft | amber-soft | Provisional pill background. |
| `--bg`, `--surface`, `--card` | neutral scale | neutral scale (inverted) | Backgrounds. |
| `--text`, `--text-muted`, `--text-dim` | neutral text scale | neutral text scale (inverted) | Foregrounds. |

Every tone token has both a background and an ink variant so pills
remain legible.

## Light-mode override pattern

Light mode is activated by `html[data-theme="light"]` (set by
`useAppTheme()`). The CSS structure is:

```css
:root {
  --bg: #0b1220;          /* dark defaults */
  --text: #e8ecf3;
  /* ... */
}

html[data-theme="light"] {
  --bg: #f4f6fb;
  --text: #0b1220;
  /* only override what changes */
}
```

All components use `var(...)` tokens, never hex literals. This is why
switching `data-theme` changes the whole app at once without reflows.

Light mode was broken once because the `--amber-ink` token was missing
from the `html[data-theme="light"]` block; the provisional status text
then inherited a dark token against a light background. The fix was
adding `--amber-ink` to both blocks. The rule is: **every token that
appears in `:root` must also be overridden (or kept identical) under
`html[data-theme="light"]`.**

## Spacing and typography

- Root font size is `clamp(15px, 1vw + 12px, 17px)` so the UI scales on
  laptop viewports without becoming giant on 4K.
- Primary font is `Inter` (loaded via Nuxt app head), with
  `system-ui` fallbacks.
- Spacing uses a 4px grid via `--space-1` (4px) through `--space-8`
  (64px).

## Component tone contract

- **StatusPill** uses `--pass-bg`/`--pass-ink`,
  `--provisional-bg`/`--amber-ink`, `--fail-bg`/`--fail-ink`.
- **RingStat / BarStat** derive `tone` from the gate pass rule; the
  same three tokens apply.
- **CollapsibleCard** uses `--surface` for its base and `--card` for
  the expanded body so hierarchy reads at a glance.

## Why Michigan maize-blue

The deliverable is being presented at the University of Michigan's PJTL
project track. Using the school palette is a direct tie-in. It also
happens to be a sharp combination for dashboard UI: high-contrast maize
reads as an attention highlight against the navy surfaces without ever
looking like a "status" color (that space is reserved for green / amber
/ red).

Decision captured in
[decision-records/0004-maize-blue-branding.md](../decision-records/0004-maize-blue-branding.md).

## Adding a new token

1. Add it to `:root` in
   [code/frontend/assets/css/main.css](../../frontend/assets/css/main.css).
2. Add a corresponding override under `html[data-theme="light"]`, even
   if the value is identical, so the contract holds.
3. Use it via `var(--your-token)` in component CSS; never hardcode hex.
4. Mention the token in this file.
