<!--
Realistic time budget: ~36 hours from spec freeze (2026-05-21 ~16:00 WIB) to ALGOfest deadline (2026-05-23 04:00 WIB).
Solo developer. Effective coding budget after sleep, meals, and video production: ~18 hours.
**CUT-LINE rule**: at hour 14 of coding, drop any task tagged [CUTLINE] that is not yet started.
**HARD FLOOR**: tasks tagged [HARDFLOOR] in §10 must ship no matter what.
SSH host alias: `vpsgw`. Live demo subdomain: `gizigo.jmola.my.id`.
LLM gateway: `http://43.228.214.145:8317/v1`, model `gpt-5.4-mini`, key in `.env`.
-->

## 1. Phase 0 — Repository Bootstrap (1.5h)

- [x] 1.1 Initialize git repo at the workspace root with `.gitignore` (Python venv, node_modules, .env, .DS_Store, dist, build, raw scrape cache), and an empty `README.md` placeholder
- [x] 1.2 Create directories: `services/api/`, `apps/web/`, `data/raw/panganku/`, `data/normalized/`, `data/akg/`, `data/prices/`, `prompts/`, `docs/`, `scripts/`
- [x] 1.3 Author top-level `Makefile` with targets: `bootstrap`, `data`, `api-dev`, `web-dev`, `lint`, `test`, `deploy`, `submission-bundle`
- [x] 1.4 Add `services/api/pyproject.toml` (Python 3.12) with deps: `fastapi`, `uvicorn`, `pulp`, `pydantic`, `asyncpg`, `pyyaml`, `pandas`, `httpx`, `beautifulsoup4`, `lxml`, `python-dotenv`; dev deps: `pytest`, `pytest-asyncio`, `ruff`
- [x] 1.5 Scaffold `apps/web/` with `pnpm create vite@latest apps/web -- --template react-ts`, then add `tailwindcss`, `@tailwindcss/forms`, `recharts`, `zod`, `lucide-react`, `clsx`, `class-variance-authority`, `sonner` (toast)
- [x] 1.6 Author `.env.example` for both api and web documenting `OPENAI_BASE_URL=http://43.228.214.145:8317/v1`, `OPENAI_API_KEY=sk-ama`, `OPENAI_MODEL=gpt-5.4-mini`, `DATABASE_URL=postgresql://gizigo:devpw@127.0.0.1:5433/gizigo`, `VITE_API_BASE_URL`, `CORS_ALLOWED_ORIGIN=https://gizigo.jmola.my.id`, `HUMANIZER_LLM_ENABLED=false`
- [x] 1.7 Local Postgres via Docker: author `scripts/docker-postgres.sh` running `docker run --rm -d --name gizigo-pg -p 5433:5432 -e POSTGRES_PASSWORD=devpw -e POSTGRES_USER=gizigo -e POSTGRES_DB=gizigo postgres:16`; on first run also execute `scripts/db-init.sql` creating the `plans` table
- [x] 1.8 Verify `make bootstrap` runs end-to-end clean (Python venv installs, pnpm installs, Postgres container starts, db-init runs); push the empty scaffold to GitHub when the user provides the remote URL

## 2. Phase 1 — Data Pipeline (3h)

- [ ] 2.1 Implement `services/api/scripts/scrape_panganku.py` performing a one-shot polite scrape of `https://www.panganku.org/id-ID/semua_nutrisi` (1-second delay between requests, `User-Agent: GiziGo/0.1 (hackathon-algofest)`); persist each ingredient detail page as raw HTML under `data/raw/panganku/<food_code>.html` and the index page under `data/raw/panganku/_index.html`
- [ ] 2.2 Implement `services/api/scripts/normalize_panganku.py` parsing the cached HTML with `beautifulsoup4`, extracting per-ingredient: `food_code` (e.g. `AM002`), display name, food group (mapped from the panganku group prefix), and the eight tracked nutrients per 100g; write `data/normalized/ingredients.json` with stable `ingredient_id = "tkpi_" + food_code`
- [ ] 2.3 Inside the normalizer, quarantine rows with negative values, missing nutrients, or unit mismatches; emit `data/validation-report.json` with row-level reasons
- [ ] 2.4 Author `data/akg/permenkes-28-2019.json` covering the seven required member categories (`toddler_1_3`, `child_4_6`, `teen_male_13_15`, `teen_female_13_15`, `adult_male_19_49`, `adult_female_19_49`, `lactating_mother_0_6m`) with the eight tracked nutrients each
- [ ] 2.5 Curate `data/prices/dki-jakarta.yaml` and `data/prices/national-baseline.yaml` from PIHPS / BPS; each covers ≥70% of the normalized catalog
- [ ] 2.6 Author `data/substitutes.yaml` covering at least 30 common Indonesian ingredient swaps with `from`, `to[]`, and `reason`
- [ ] 2.7 Author `data/cooking-method.yaml` mapping at least 60 common ingredients to one of the five cooking verbs (`tumis`, `rebus`, `kukus`, `goreng`, `sangrai`); include a food-group fallback section for ingredients not individually listed
- [ ] 2.8 Wire `make data` to run scrape (cached, idempotent) → normalize → validate → assert byte-stable normalized output on a clean re-run; commit normalized artifacts and `data/raw/panganku/` to the repo
- [ ] 2.9 Begin `data/MANIFEST.md` with Phase 1 entries: TKPI 2020 (Kemenkes, ISBN 978-623-301-0368) as upstream regulatory source, `panganku.org` as technical retrieval channel, AKG citation, price-snapshot sources

## 3. Phase 2 — Core ILP Optimizer (4h)

- [ ] 3.1 Define Pydantic models in `services/api/src/models.py`: `HouseholdMember` (with the seven member-category enum), `HouseholdProfile`, `Restrictions`, `Plan`, `MealItem`, `OptimizeRequest`, `OptimizeResponse`, `InfeasibilityReport`, `SensitivityRequest`, plus `DiverseRelaxation { relaxed: bool, reason?: "budget_exhausted" | "akg_bound_violated" }`
- [ ] 3.2 Implement `services/api/src/optimizer/akg.py` aggregating AKG requirements across household members for the eight tracked nutrients, applying the lactation 0-6m supplement explicitly (+330 kcal, +0.4mg iron, etc.)
- [ ] 3.3 Implement `services/api/src/optimizer/constraints.py` computing the hard-exclusion ingredient set from `Restrictions` (halal, allergies, regional availability)
- [ ] 3.4 Implement `services/api/src/optimizer/ilp.py` building the PuLP model: continuous gram variables ≥0 per ingredient × meal slot, AKG lower-bound rows, budget upper-bound row; expose `solve_cheapest()` and `solve_balanced()` returning `Plan | None`. NO Big-M / no binary food-group indicators in this module — `solve_diverse` is implemented as a heuristic in 3.6
- [ ] 3.5 In `solve_balanced`, formulate the objective as `min(total_cost + alpha * sum(slack_i))` with auxiliary slack variables `slack_i >= 0` and constraints `slack_i >= AKG_i - achieved_i`; document `alpha` calibration so a 1-rupiah cost increase trades against a 1% nutrient deficit
- [ ] 3.6 Implement `services/api/src/optimizer/diversify.py` providing `derive_diverse(cheapest_plan, catalog, prices, akg_required, budget) -> (Plan, DiverseRelaxation)`: iteratively pick the lowest-nutrient-density-per-rupiah ingredient in the current plan, attempt swaps for ingredients from previously-unused food groups, accept the swap if AKG bounds remain satisfied and budget not exceeded, otherwise try the next candidate; tie-break deterministically by `ingredient_id` ascending; halt when `count_groups ≥ count_groups(cheapest) + 2` or no feasible swap exists; emit relaxation metadata
- [ ] 3.7 Implement `services/api/src/optimizer/infeasibility.py`: when `solve_cheapest` is infeasible, run a feasibility-only LP minimizing the maximum nutrient-deficit ratio to identify failing nutrients; bisect on budget to compute `minimum_budget_delta_rupiah`
- [ ] 3.8 Implement `services/api/src/optimizer/hashing.py`: deterministic SHA-256 of canonicalized inputs and outputs for `plan_hash`
- [ ] 3.9 Pin solver options for determinism: CBC `randomSeed` fixed, `threads=1`, `presolve=on`, `cuts=off`; pin Python `hash` randomization off via `PYTHONHASHSEED=0` in run scripts
- [ ] 3.10 Tests under `services/api/tests/optimizer/`: feasibility test, infeasibility test, halal-constraint test, allergy test, determinism test (twice = byte-equal), sensitivity-shock test, lactation-supplement test, diversify heuristic test (assert ≥ +2 groups OR `relaxed: true` with reason)

## 4. Phase 3 — API Surface (1.5h)

- [ ] 4.1 Implement `services/api/src/main.py` bootstrapping FastAPI, CORS using `CORS_ALLOWED_ORIGIN`, request-id middleware, structured logging
- [ ] 4.2 Implement `POST /v1/optimize`: solve `cheapest` + `balanced` ILPs and `diverse` heuristic, persist `(plan_hash, request_json, response_json)` to `plans`, return cached responses on hit with `cache: true`
- [ ] 4.3 Implement `POST /v1/sensitivity`: accept `baseline_request + price_shock + budget_delta_rupiah`, mutate the price view, re-solve, return new plans plus `baseline_plan_hash`
- [ ] 4.4 Implement `POST /v1/humanize` (delegates to Phase 7) and `GET /v1/health` (returns version, data-version checksums, solver name, uptime, llm_enabled flag)
- [ ] 4.5 Define the structured-error envelope `{ error_code, message, request_id, details? }`; convert FastAPI validation errors via an exception handler; messages SHALL be Bahasa Indonesia
- [ ] 4.6 Smoke-test endpoints with `scripts/smoke-test.sh` (curl-based); confirm `/openapi.json` and `/docs` render with schemas

## 5. Phase 4 — Front-End Skeleton (4h)

- [ ] 5.1 Configure Tailwind tokens, dark/light themes, font stack (Plus Jakarta Sans via Google Fonts CDN), color palette ≥4.5:1 contrast for body text
- [ ] 5.2 Add shadcn-style copy-paste primitives (`button`, `card`, `accordion`, `slider`, `dialog`, `drawer`, `select`, `input`, `chip`, `skeleton`, `toast`) under `apps/web/src/components/ui/`; wire `sonner` `<Toaster />` into the root
- [ ] 5.3 Implement `apps/web/src/lib/api-client.ts` typed via `zod` schemas for `Optimize`, `Sensitivity`, `Humanize`, `Health` plus `useOptimize`, `useSensitivity`, `useHumanize`, `useHealth` hooks (custom, no react-query — use `useState` + `useEffect`); on any non-2xx, fire a `toast.error` with the API `message` field and a "Coba lagi" action
- [ ] 5.4 Implement the household form component: dynamic member rows (member-category select, count), region select, restrictions checkboxes (halal default ON, allergies multi-select with `peanut`, `seafood`, `dairy`, `egg`)
- [ ] 5.5 Implement the budget input as slider (Rp 1,000 increments) bound bidirectionally with a numeric input
- [ ] 5.6 Implement the persona quick-start menu with the two demo personas; selecting populates the form and triggers `/v1/optimize`
- [ ] 5.7 Centralize all visible copy in `apps/web/src/copy/id.ts`; no inline strings outside this module
- [ ] 5.8 Implement loading and empty states: a hero card explaining the product when no inputs entered yet, three plan-card skeletons during solve (500-1500ms perceived), and "API tidak tersedia" toast on network failure with retry button
- [ ] 5.9 Wire the form submit and run a happy-path optimize call against the local API; confirm three plans land in state

## 6. Phase 5 — Plan Cards, AKG Visualization, Sensitivity (4h)

- [ ] 6.1 Implement `PlanCard` rendering `Termurah`, `Paling Seimbang`, `Paling Beragam` titles, currency-formatted `total_cost_rupiah`, eight horizontal AKG bars per nutrient
- [ ] 6.2 AKG bars: 0-100% in neutral color, 100% in accent color, >100% with a subtle gradient/badge — no color-only meaning (also use a check icon at 100%, an arrow icon for >100%)
- [ ] 6.3 Implement the meal-slot accordion inside each card: `Sarapan`, `Makan Siang`, `Makan Malam` with ingredient rows showing display name, grams, per-member portion hint
- [ ] 6.4 Render a small badge on the `Paling Beragam` card when `diverse_constraint_relaxed: true`, with hover tooltip explaining the reason in Bahasa Indonesia
- [ ] 6.5 Implement the global sensitivity bar fixed below the form: budget slider with 200ms debounce re-issuing `/v1/sensitivity`
- [ ] 6.6 Implement two preset price-shock chips (`Cabai +50%`, `Telur −10%`); toggle re-issues `/v1/sensitivity`
- [ ] 6.7 Render substitution badges on ingredient rows when a sensitivity-driven swap occurs vs. baseline
- [ ] 6.8 Smoke-test on a 360px viewport (Chrome devtools); fix any layout breaks

## 7. Phase 6 — Infeasibility Panel + Recipe Drawer (1.5h)

- [ ] 7.1 Implement `InfeasibilityPanel`: list each failing nutrient with labeled progress bar, gap value, recommended `minimum_budget_delta_rupiah`
- [ ] 7.2 Add the "Naikkan budget ke Rp X" action: sets the slider to the recommended amount and triggers a fresh `/v1/optimize`
- [ ] 7.3 Implement `RecipeDrawer` opened from a slot row click: shows humanized recipe text, per-member portions, substitution chips
- [ ] 7.4 Wire keyboard-only flow: ESC closes drawer, focus trap inside drawer, focus restored on close

## 8. Phase 7 — Humanizer (templated + LLM upgrade) (1.5h)

- [ ] 8.1 Implement `services/api/src/humanizer/templated.py` deterministic Bahasa Indonesia rendering: load `data/cooking-method.yaml` for ingredient → cooking verb mapping (with food-group fallback), use one template per cooking verb (`tumis`, `rebus`, `kukus`, `goreng`, `sangrai`); per-member portions split via AKG-weighted shares
- [ ] 8.2 Implement `services/api/src/humanizer/main.py` exposing `humanize(plan, household) -> { recipes, humanization_mode, validation? }`; default mode is `templated`
- [ ] 8.3 [CUTLINE] Implement `services/api/src/humanizer/llm.py` calling `OPENAI_BASE_URL` with `OPENAI_MODEL=gpt-5.4-mini`, temperature 0.2, 6s timeout; prompt at `prompts/humanize-system.md` + `prompts/humanize-fewshot.md`
- [ ] 8.4 [CUTLINE] Implement `services/api/src/humanizer/validator.py` re-extracting ingredient grams from LLM output; >5% drift OR missing ingredient → discard LLM, return templated
- [ ] 8.5 Substitution lookup uses `data/substitutes.yaml` directly — return up to three substitutes per ingredient with reason

## 9. Phase 8 — VPS Deployment (2h, increased from 1.5h to cover certbot + docker pg)

- [ ] 9.1 SSH to `vpsgw`: confirm Docker, nginx, and certbot are installed; install Python 3.12 if missing
- [ ] 9.2 Provision Postgres on the VPS via Docker: `docker run -d --name gizigo-pg --restart=always -p 127.0.0.1:5432:5432 -e POSTGRES_PASSWORD=<from vault> -e POSTGRES_USER=gizigo -e POSTGRES_DB=gizigo -v /var/lib/gizigo-pg:/var/lib/postgresql/data postgres:16`; run `db-init.sql`
- [ ] 9.3 Clone the repo to `~/gizigo/`, create Python venv at `~/gizigo/services/api/.venv`, install API deps from `pyproject.toml`, run `make data` once
- [ ] 9.4 Author `services/api/scripts/run-prod.sh` running `uvicorn` with `--workers 2 --host 127.0.0.1 --port 8001`; create `gizigo-api.service` systemd unit with `Restart=on-failure` and `EnvironmentFile=~/gizigo/.env`; `systemctl enable --now gizigo-api`
- [ ] 9.5 Author `apps/web/scripts/build-prod.sh` running `pnpm install --frozen-lockfile && pnpm build` and copying `dist/` to `/var/www/gizigo/`
- [ ] 9.6 Configure nginx site `/etc/nginx/sites-available/gizigo.jmola.my.id`: serve `/var/www/gizigo/` for `/`, proxy `/v1/*` to `http://127.0.0.1:8001/v1/*`, enable `gzip`, set `Cache-Control: no-cache` for `index.html`; `nginx -t && systemctl reload nginx`
- [ ] 9.7 Issue TLS cert: `sudo certbot --nginx -d gizigo.jmola.my.id --non-interactive --agree-tos --email <user-email>`; verify auto-renewal cron is in place
- [ ] 9.8 Run `scripts/deploy.sh` end-to-end; hit `https://gizigo.jmola.my.id/v1/health` from a phone to confirm; smoke-test the two demo personas through the UI

## 10. Phase 9 — README, Demo Video, Submission (5h)

- [ ] 10.1 [HARDFLOOR] Author `README.md` with anchored sections mapped to the rubric: `# Innovation`, `# Technical Complexity`, `# Practical Impact`, `# Design & UX`, `# Demo`, plus `# Quickstart`, `# Architecture`, `# Data Sources`, `# Reproducibility`, `# Roadmap`
- [ ] 10.2 [HARDFLOOR] Embed three hero screenshots (form filled, three plans rendered, infeasibility panel) and one architecture diagram (`docs/architecture.svg` — simple boxes, no overengineering) inline in README
- [ ] 10.3 [HARDFLOOR] Author `docs/ilp-formulation.md`: variables, constraints, two ILP objectives, diversification heuristic pseudocode, infeasibility analyzer, complexity discussion, 1 worked example
- [ ] 10.4 [HARDFLOOR] Author `docs/data-sources.md` listing TKPI 2020 (Kemenkes book ISBN 978-623-301-0368, retrieved via panganku.org), AKG citation (Permenkes 28/2019), price-snapshot sources with retrieval dates, all licenses
- [ ] 10.5 [HARDFLOOR] Finalize `data/MANIFEST.md` with the full provenance trail
- [ ] 10.6 [HARDFLOOR] Author `docs/demo-script.md`: 3-minute shot list, voiceover lines in English with optional Bahasa subtitles, mapped to each rubric criterion
- [ ] 10.7 [HARDFLOOR] Record screen captures: persona selection → three plans, sensitivity slider sweep, cabai shock chip, infeasibility panel + budget bump, recipe drawer
- [ ] 10.8 [HARDFLOOR] Record voiceover (English, 165-180 wpm) and assemble in OBS / DaVinci Resolve / iMovie; export 1080p H.264 ≤ 200 MB
- [ ] 10.9 [HARDFLOOR] Upload to YouTube unlisted; embed the link in README and Devpost submission
- [ ] 10.10 [HARDFLOOR] Author the Devpost submission body: 3-paragraph elevator pitch (problem, solution, why ALGOfest), bullet feature list, technologies used, team details (solo)
- [ ] 10.11 [HARDFLOOR] Submit on Devpost: title, tagline, description, video URL, repo URL, live demo URL `https://gizigo.jmola.my.id`, technologies, team
- [ ] 10.12 [HARDFLOOR] Hold final review at T-2h before deadline; resubmit with corrections if any field rejected

## 11. Cut-Line Tasks (drop in this order if behind schedule at hour 14 of coding)

- [ ] 11.1 [CUTLINE] LLM humanizer (8.3, 8.4) — ship templated rendering only, frame as "deterministic by design" in README
- [ ] 11.2 [CUTLINE] `Paling Beragam` heuristic (3.6, 6.4) — fall back to returning two plans (`Termurah` + `Paling Seimbang`) and explicitly note the third is a roadmap item
- [ ] 11.3 [CUTLINE] Mobile-360 layout polish (6.8) — desktop-first only, surface a "Best on desktop" banner on mobile
- [ ] 11.4 [CUTLINE] Architecture SVG (10.2) — replace with an ASCII-art block diagram inside the README
- [ ] 11.5 [CUTLINE] Recipe drawer keyboard focus trap (7.4) — keep ESC-to-close only

## 12. Hard Floor — These Must Ship No Matter What

- [ ] 12.1 [HARDFLOOR] Working `/v1/optimize` endpoint with at least the `Termurah` and `Paling Seimbang` plans + infeasibility report
- [ ] 12.2 [HARDFLOOR] Working web UI with household form, plan cards, budget slider, infeasibility panel, error toast, loading skeletons
- [ ] 12.3 [HARDFLOOR] Both demo personas working end-to-end against the live VPS deploy at `https://gizigo.jmola.my.id`
- [ ] 12.4 [HARDFLOOR] README with rubric-mapped sections and three screenshots
- [ ] 12.5 [HARDFLOOR] 3-minute demo video uploaded
- [ ] 12.6 [HARDFLOOR] Devpost submission completed before T-2h
