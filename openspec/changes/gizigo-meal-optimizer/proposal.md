## Why

21.6% of Indonesian children under five are stunted (Riskesdas / SSGI 2024) — a chronic-malnutrition rate among the world's worst. The root cause for the bottom-40% income tier is rarely lack of will: it is information asymmetry. A mother with Rp 25,000/day cannot translate Kemenkes' Angka Kecukupan Gizi (AKG) into a real shopping list against fluctuating wet-market prices. Existing meal-planning apps target middle-class urban users with calorie counters, not nutrient-density-per-rupiah for the mothers who actually need it.

This is also the right time and the right hackathon: ALGOfest 2026's rubric weighs **Innovation & Creativity** and **Presentation & Documentation** — exactly the two axes a deterministic Operations Research solver wins on, against a field of GPT-wrappers. The dataset (Kemenkes TKPI, AKG-2019, PIHPS price reports) is public, the math is honest, and the demo lives or dies by a single 3-minute video plus a clean README.

## What Changes

- **Add** a deterministic Integer Linear Programming meal-plan optimizer: given a household profile, daily budget, region, and dietary restrictions, return a daily plan (sarapan, makan siang, makan malam) that satisfies AKG nutrient lower bounds while respecting budget.
- **Add** a three-plan Pareto presentation: `Termurah` (minimum cost), `Paling Seimbang` (best nutrient-adequacy under budget via weighted-sum objective), `Paling Beragam` (constraint-based diversification on top of the cheapest plan).
- **Add** a sensitivity re-solve path: budget slider and two preset price-shock chips (`cabai +50%`, `telur −10%`) re-issue the solver with mutated inputs in <500ms.
- **Add** an infeasibility transparency report: when AKG cannot be met under the budget, identify failing nutrients and the minimum budget delta required to restore feasibility.
- **Add** a templated Bahasa Indonesia humanization layer that converts the structured plan into recipe text and per-member portions; an optional LLM enrichment via the user's OpenAI-compatible gateway is gated behind validation against the source plan.
- **Add** a hand-curated substitution table (no embedding/vector index) covering the 30 most-common ingredient swaps for regional availability.
- **Add** a single-page Vite + React + Tailwind front-end optimized for the 2-5 minute submission video, with two demo personas, a budget slider, three plan cards, and an infeasibility panel.

## Capabilities

### New Capabilities

- `meal-optimizer`: Solves the nutrition-vs-budget ILP. Owns the constraint model (AKG bounds, halal/allergy hard rules, regional availability), the three single-objective solves, and the infeasibility analyzer.
- `nutrition-data`: Loads, validates, and serves the TKPI nutrient catalog, an AKG subset covering the demo personas (toddler 1-3y, child 4-6y, teen 13-15y, adult 19-49y, lactating 0-6m), one regional price snapshot (DKI Jakarta) plus a national baseline, and a hand-curated substitution table.
- `meal-humanizer`: Renders structured plans as Bahasa Indonesia recipes and grocery lists. Templated rendering is the default and only required path; an LLM upgrade via `OPENAI_BASE_URL` is optional and validated against the source plan.
- `optimizer-api`: HTTP surface (FastAPI) exposing `/v1/optimize`, `/v1/sensitivity`, `/v1/humanize`, `/v1/health`. Backed by Postgres for plan caching keyed on a deterministic hash.
- `optimizer-web`: Vite + React + Tailwind single-page app with the household form, region selector, budget slider, two preset shock chips, three plan cards, infeasibility panel, recipe drawer, and two pre-filled demo personas.

### Modified Capabilities

<!-- None — greenfield project. -->

## Impact

- **New code**: `apps/web/` (Vite + React 18 + Tailwind + shadcn-via-cli + Recharts), `services/api/` (FastAPI + PuLP + asyncpg + httpx for the panganku scraper), `data/` (raw scraped HTML, normalized JSON, AKG subset JSON, Jakarta + national-baseline price YAML, substitution table YAML, cooking-method YAML), `prompts/` (humanizer templates).
- **Dependencies**: PuLP (CBC solver, MIT), pandas, fastapi, asyncpg, pyyaml, httpx, beautifulsoup4 (panganku scraper), pydantic; React 18, Tailwind, recharts, zod, lucide-react.
- **Infrastructure**: User-owned VPS reachable via SSH alias `vpsgw` for domain `jmola.my.id` (subdomain `gizigo.jmola.my.id`). Existing nginx is reused. Postgres 16 runs as a Docker container on the VPS (Docker is already installed), exposing port 5432 to localhost only. The static Vite build is served from `/var/www/gizigo/`. Certbot is installed but the cert for the new subdomain has not yet been issued; a deploy task issues it. No Caddy, no PaaS, no managed database.
- **External services**: User-provided OpenAI-compatible gateway at `http://43.228.214.145:8317/v1` (model `gpt-5.4-mini`) for the optional humanizer enrichment only. The optimizer is fully deterministic and runs without internet.
- **Data**: Tabel Komposisi Pangan Indonesia (TKPI 2020) sourced from Kemenkes via `panganku.org/id-ID/semua_nutrisi` (one-shot HTML scrape, output committed under `data/raw/panganku/`), AKG values from Permenkes 28/2019 (subset, seven member categories), price snapshots from PIHPS/BPS published values for DKI Jakarta plus a national-baseline average. No PII collected.
- **Out of scope (this change)**: User accounts, plan history beyond the plan-hash cache, mobile app, real-time price scraping, payment integration, vector-embedding substitutions (replaced by a hand-curated table), full Permenkes age-band coverage, custom price-shock dialog, framer-motion animation, URL query-string sharing, axe-core accessibility audit, Prometheus instrumentation, Docker for the application code itself, multi-language support.
