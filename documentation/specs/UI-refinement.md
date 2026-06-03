# Spec — UI Atmosphere Refinement: the Living Blue Orb

Status: planned
Author: Cosmos De La Cruz
Date: 2026-06-03
Skills used: `frontend-design`, `ui-ux-pro-max`

## Why

SophiaAI already ships a coherent cosmic UI: glass panels, a CSS orb, a canvas
starfield, three-panel chat (`sophia/app/static/css/sophia.css`, 880 lines,
fully token-driven). It works. But the *atmosphere* drifts from the visual
identity in `SophiaAI Atmosphere/`.

The reference assets say one thing loudly: **Sophia is a living blue orb of
light, floating in a deep indigo void, touched by gold divinity.** The current
UI says something softer and less focused — a **violet/magenta** gradient
identity (buttons, glows, brand shadow all lean purple-pink). The orb is blue,
but everything around it pulls toward purple, so the orb does not read as *the*
hero. Gold — the colour of the goddess's halo and the divine light in every
reference image — is demoted to a minor pillar accent.

This is not a rebuild. It is a **re-weighting of the existing design system**:
make electric blue the dominant luminance, deepen the void, promote gold to the
sacred accent, and turn the orb + wordmark into the two things a visitor
remembers. Because components read tokens only (no raw hex in components — a
locked convention), most of the shift happens in `:root`.

### What the assets establish (the atmosphere)

| Asset | What it contributes |
|---|---|
| `glowing-energy-orb`, `glowing-blue-orb`, `2D366…` (orb in hand) | The hero motif: an electric-blue plasma sphere with arcing energy and a breathing glow. Blue-white core. |
| `cosmic_sophia`, `E18ACE…`, `black_holes` | Deep indigo void, black-hole accretion swirl, blue→gold particle streams. Background depth. |
| `sophia_aura` (blue ring + glowing SOPHIA) | Wordmark direction: elegant serif, cyan **and** gold dual glow, generous tracking. |
| `IMG_1794` (marble goddess, gold astrolabe halo, lotus, cosmic orb) | The divine/sacred layer: marble + **gold** sacred-geometry halo over indigo. |
| `COSMOS`, `IMG_6249`, `6E63AF…` | Nebula/galaxy texture — stars in blue-white with warm gold highlights. |

## Aesthetic direction (committed)

One sentence: **a luminous blue intelligence breathing in a sacred indigo
void.** Refined-mystical, not maximalist. Restraint is the point — depth and
glow do the work, not clutter.

- **Dominant:** electric blue / cyan (the orb).
- **Sacred accent:** gold (halo, divine light, "primary source of truth"
  moments — citations, the corpus).
- **Secondary:** violet/magenta survive but step back — used for the human side
  (user bubbles, secondary CTAs) so blue/gold own Sophia's side.
- **Surface:** deeper, more saturated indigo void than today.

## Decisions (confirm before build — see open questions)

1. **Token re-weighting, not a new palette.** Keep `--violet`, `--cyan`,
   `--magenta`, `--gold`; add a true electric-blue token and a gold-glow token;
   re-point the *semantic* tokens (primary action, brand glow, Sophia accent) at
   blue + gold. Components are untouched because they already read tokens.
2. **Orb stays pure CSS/SVG.** No raster orb asset. Matches the existing
   approach + the "no Ferrari to the corner store" performance ethos. We enrich
   the existing `.orb` (core, plasma ring, glow) with a second arc layer and a
   stronger idle breathe.
3. **Wordmark = CSS, no image.** Gradient text + layered dual-glow text-shadow
   (cyan + gold) on `.brand` and `.hero-copy h1`. Keeps it crisp at any size and
   theme-able; avoids a raster that pixelates (ui-ux-pro-max `vector-only`).
4. **Fonts unchanged.** Cinzel (display/brand) is already a distinctive,
   characterful serif that fits the mystical tone — it is *not* generic AI slop,
   so the frontend-design "avoid Inter/Roboto" caution is already satisfied on
   the display side. Inter stays as the body workhorse. No font churn.
5. **Background: CSS-first, one optional image.** Deepen the layered radial
   gradients (blue + indigo + a faint gold high), keep the canvas starfield,
   add a faint gold halo-ring behind the large orb on the empty state. A nebula
   raster is *optional* and gated on weight (see open questions).

## Scope phases

Build in order; each phase is independently shippable and reversible.

### Phase 1 — Palette & tokens (the big lever)
File: `sophia/app/static/css/sophia.css` `:root`.

- Add tokens:
  - `--azure: #2b8bff;` (electric blue — already the orb core colour, promote it
    to a named token)
  - `--azure-bright: #7fe8ff;`
  - `--gold-glow: rgba(201,162,39,0.55);`
  - `--blue-glow: rgba(43,139,255,0.55);`
- Deepen the void: nudge `--void`/`--void-2` bluer + darker (e.g.
  `--void: #050414; --void-2: #080726;`) — verify contrast after (see a11y).
- Re-point semantics toward blue/gold:
  - Brand/hero glow: violet → `--blue-glow` (+ a faint gold under-glow).
  - Glass border `--glass-brd`: violet tint → azure tint.
  - `--pillar-science` stays gold; consider gold as the **citation/source**
    colour globally (it already is on `.source .pillar`), reinforcing
    "gold = grounded truth".
- **Keep** `--violet`/`--magenta` for the human side (user bubble, secondary).

### Phase 2 — The Orb as hero
File: `sophia/app/static/css/sophia.css` `.orb` + `@keyframes`.

- Enrich `.orb`: keep core gradient; add a second `::before`/layer for **plasma
  arcs** (a second conic gradient at a different speed) to echo the energy-orb
  assets; strengthen the `::after` glow halo (larger, bluer).
- Tune motion (all already gated behind `prefers-reduced-motion`):
  - `idle`: slower, deeper breathe (scale + glow opacity).
  - `thinking`: faster spin + brighter halo pulse (already present — intensify).
- `.orb-lg` on the empty state: add a concentric **gold sacred-geometry ring**
  (thin `border` + `radial-gradient` halo, or a small inline SVG astrolabe ring)
  echoing the goddess halo in `IMG_1794`. Decorative → `aria-hidden`, motion
  gated.

### Phase 3 — Wordmark & hero
Files: `sophia/app/static/css/sophia.css` (`.brand`, `.hero-copy h1`),
optionally `templates/index.html`.

- `.brand` and hero `h1`: gradient text (white→azure→gold) via
  `background-clip: text` with a solid-colour fallback, plus dual-glow
  text-shadow (cyan + gold). Preserve current tracking (`0.18–0.28em`).
- Hero figure: retune the `.hero-figure::after` glow from violet → blue+gold to
  frame the goddess image (`sophia_goddess.jpg`) in divine light.

### Phase 4 — Background depth & glass
File: `sophia/app/static/css/sophia.css` (`body`, `.glass`),
optionally `static/js/cosmos.js`.

- `body` background: re-layer the radial gradients — a large azure bloom top, a
  deep indigo base, a faint warm-gold high near where the orb sits. Optional
  subtle vignette for depth (avoid muddying contrast).
- `.glass`: shift border/shadow toward azure; add a faint inner top-glow so
  panels feel lit from within. Keep blur modest (perf).
- Starfield (`cosmos.js`): tint a *minority* of stars warm-gold among the
  blue-white, and add an occasional brighter "twinkle" — small, optional, still
  reduced-motion aware (paint one static frame when reduced).

## Files touched

| File | Change |
|---|---|
| `sophia/app/static/css/sophia.css` | New tokens; deepen void; re-point brand/glass/glow semantics to blue+gold; enrich `.orb` (arcs, halo, gold ring); gradient+glow wordmark; deeper background layers; lit glass |
| `sophia/app/templates/index.html` | (Optional) hero markup tweak if wordmark needs an extra span for gradient/glow layering |
| `sophia/app/static/js/cosmos.js` | (Optional, Phase 4) gold-tinted minority stars + occasional twinkle, reduced-motion safe |
| `sophia/app/static/img/` | (Optional) one curated nebula/halo asset only if the CSS-first background is judged too flat — see open questions |

No backend, no templates logic, no endpoints, no tests-of-record change (UI is
not under unit test today). No new dependencies.

## Constraints that must hold (do not break)

- **Tokens-only-in-components stays.** All new colour goes in `:root`; components
  keep reading variables. No raw hex added inside component rules.
- **`prefers-reduced-motion`** must gate every new animation; reduced users get a
  single static frame (the existing pattern at css:833 and `cosmos.js`).
- **Accessibility (ui-ux-pro-max P1/P2):**
  - Body/text contrast ≥ 4.5:1 after the void is darkened — re-verify
    `--text #e8e6ff` and `--text-dim #a7a3d6` against the new void.
  - Gradient/glow on the wordmark must keep a solid-colour fallback so the brand
    is readable if `background-clip:text` is unsupported.
  - Focus rings (`:focus-visible`), 44px touch targets, and `aria-hidden` on
    decorative orb/ring all preserved.
- **No layout shift / CLS:** atmosphere changes are paint-only (colour, shadow,
  gradient, transform/opacity animation) — no width/height/top/left animation,
  no reflow (ui-ux-pro-max `transform-performance`, `layout-shift-avoid`).
- **Performance:** keep blur modest; orb arcs are CSS gradients not extra DOM;
  any image is WebP/optimized and `loading`-appropriate.
- House conventions (`from __future__` n/a for CSS/JS; Mental-Model comment
  blocks on any new JS function in `cosmos.js`; logging format n/a) intact.

## Verification

1. **Run the app** and eyeball each surface against the assets:
   `SophiaAI-venv\Scripts\Activate.ps1` then `uvicorn sophia.app.main:app
   --reload` → open `/` (hero + wordmark + goddess glow), `/login`, `/chat`
   (orb empty-state + gold ring, glass panels, Sophia avatar orb states).
2. **Orb states:** send a message; confirm idle→thinking→speaking transitions
   read as blue plasma breathing, not purple.
3. **Reduced motion:** OS "reduce motion" on → reload → confirm starfield and
   orb paint one static frame, no animation loop.
4. **Contrast pass:** check `--text`/`--text-dim` on the new void with a contrast
   tool (target ≥4.5:1 body, ≥3:1 dim/large).
5. **Responsive:** 375px, 768px, 1440px — three-panel collapses correctly, no
   horizontal scroll, wordmark glow legible on mobile.
6. **Cross-theme glow fallback:** temporarily disable `background-clip:text` (or
   test a non-supporting view) → wordmark still readable in solid colour.

## Open questions (resolve before Phase 1)

1. **Void darkness.** How deep? Near-black indigo (`#050414`, max drama, watch
   contrast) vs the current softer `#07061a`. Recommend near-black, re-verified.
2. **Nebula image.** Pure-CSS background (lightest, recommended) vs one optional
   optimized nebula raster (`COSMOS.PNG`/`IMG_6249` → WebP) behind the starfield
   for extra depth at the cost of weight?
3. **Gold sacred ring on the empty-state orb.** Pure CSS halo ring (simple) vs a
   small inline SVG astrolabe ring echoing the goddess halo (richer, more code)?
4. **Magenta's fate.** Keep violet/magenta for the human/secondary side
   (recommended — preserves contrast between Sophia's blue and the user) vs
   retire them entirely for an all-blue/gold system?
