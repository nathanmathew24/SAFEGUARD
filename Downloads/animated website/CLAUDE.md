# funoon.ai Website

Single-file marketing site (`funoon-ai-website.html`) — all CSS and JS inline. No build step, no framework. Open directly in browser.

## Design Context

### Users
UAE car dealership owners (non-technical, very busy). Land on this page on a laptop during/after business hours, evaluate ROI, decide to book a demo. They are the decision-maker and budget holder. They care about not losing deals. The site must convey authority and credibility instantly.

### Brand Personality
**Three words**: urgent · authoritative · Gulf-built

Not a chatbot company — a sales weapon for car dealerships. Should feel like the instrument panel of a premium vehicle: precise, purposeful, every detail deliberate. Not cold tech. Not playful startup.

### Aesthetic Direction
- **Theme**: Dark, warm. Not cool-dark (no cyan, no neon blue). Warm cream `oklch(95% 0.018 78)` against near-black `oklch(5.5% 0.005 58)` is the core contrast.
- **Reference**: plug.ae — surprising layout scale, editorial boldness, not another SaaS template.
- **Anti-references**: No generic SaaS. No glassmorphism. No identical card grids with emoji icons. No Inter font.

### Typography System
- **Display/headlines**: `Big Shoulders Display` (weight 800–900) — condensed industrial, commands authority. Uppercase on major headings.
- **Body**: `Lexend Deca` (weight 300–400) — designed for readability, clean without being generic.

### Color Tokens (OKLCH)
- `--bg`: `oklch(5.5% 0.005 58)` — near-black with a breath of warm amber
- `--gold`: `oklch(95% 0.018 78)` — the warm cream accent
- `--wa`: `oklch(72% 0.19 145)` — WhatsApp green (signal color, not brand color)

### Design Principles
1. **Scale is the surprise** — headlines fill the viewport. Larger than expected, bolder than comfortable.
2. **Dark and warm, never cold** — Gulf product. Never introduce blue or cool tones.
3. **Data leads conviction** — stats (67%, 6h+, 78%) are more persuasive than feature lists. Give them space.
4. **Every transition earns its smoothness** — use `--ease-out-expo: cubic-bezier(0.16, 1, 0.3, 1)` as default. Never `ease` or `linear`.
5. **Automotive precision** — no orphans, no rounding inconsistencies, no pixel-off alignment.
