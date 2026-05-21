## Context

GiziGo is a 30-hour solo build for ALGOfest 2026 (deadline 23 May 04:00 WIB / 22 May 17:00 EDT). The judging rubric on this listing is short — **Innovation & Creativity** + **Presentation and Documentation** — with Devpost scoring weighted toward a 2-5 minute demo video, README, and a deployed live demo. That tilts the engineering target away from "ship many features" and toward "one deeply visible algorithmic insight in a clean UI".

The available time is **~36 hours** from spec freeze, of which a realistic **~18 hours** can be spent coding (the rest is sleep, meals, video production, README polish, and submission). Decisions in this doc bias hard toward **boring infrastructure + one mathematically interesting core**, with explicit cut-lines for everything that does not serve the demo.

The problem domain (Indonesian childhood stunting, 21.6%) is government-priority and emotionally legible to an international jury. The dataset (Kemenkes TKPI, Permenkes 28/2019 AKG, PIHPS/BPS price reports) is small (low-thousand rows), which makes a real ILP solve tractable in a hackathon timeframe. The user has a self-hosted VPS reachable via SSH alias `vpsgw` running nginx already, plus a private OpenAI-compatible gateway at `http://43.228.214.145:8317/v1` with model `gpt-5.4-mini`.

## Goals / Non-Goals

**Goals:**

- Demonstrate **algorithmic depth that is visible** — three Pareto plans, a sensitivity slider, an infeasibility panel — so a non-technical viewer of a 3-minute demo video understands "this is solving math, not calling ChatGPT".
- Hit **three prize tracks in parallel**: Top 3 cash, Best HealthTech ($100), Best Social Impact special award.
- Produce a **deployable artifact** (web app + API on VPS) and a **public GitHub repo** with a README structured around the rubric.
- Stay **deterministic**: the optimizer must produce the same plan for the same inputs every time. The LLM, when used at all, only humanizes — never decides.
- Localize for Indonesia: copy in Bahasa Indonesia, currency in Rupiah, ingredients from TKPI, AKG from Permenkes 28/2019.

**Non-Goals:**

- User accounts, login, plan history persistence beyond the plan-hash cache.
- Mobile-native app (a mobile-friendly responsive web is in scope; native is not).
- Real-time price scraping. We use a curated price snapshot committed to the repo. Live pricing is a v2 narrative.
- Payment integration, e-commerce, grocery delivery API.
- Multi-language. Bahasa Indonesia only. The README and demo video MAY include English subtitles.
- Recipe novelty. We map ILP output to existing well-known Indonesian dishes (sayur bayam, tempe goreng, telur balado). The LLM does not invent recipes.
- Medical advice for clinical malnutrition. The product is a planning aid; severe-malnutrition cases are referred to puskesmas in the UI copy.
- Vector-embedding substitution (replaced by a hand-curated table for time).
- Docker, Caddy, Vercel, Railway. We deploy directly to the existing VPS with nginx.

## Decisions

### Decision 1: ILP via PuLP + CBC, not heuristic / ML / LLM

**Choice**: Formulate the meal plan as a Mixed-Integer Linear Program. Variables are ingredient grams per meal slot. Constraints are AKG nutrient lower bounds (energy, protein, fat, carbohydrate, iron, zinc, vitamin A, calcium), budget upper bound, halal/allergy hard rules, regional availability. We solve three single-objective ILPs to materialize the Pareto frontier instead of one weighted multi-objective.

**Rationale**: PuLP+CBC is MIT-licensed, ships in a single `pip install`, and solves problems of this size (~200 ingredients × 3 meal slots = ~600 variables) in well under 500ms. ILP gives **provable optimality**, which is the algorithmic claim the judges can verify by reading the code.

**Alternatives considered**: Genetic algorithms, simulated annealing, LLM-as-optimizer, pure greedy heuristic. All rejected — either no optimality guarantee (heuristics), non-determinism (LLM), or unintelligible to a 3-minute demo.

### Decision 2: Three plans materialized as two ILPs + one heuristic, not three MILPs

**Choice**:
- `Termurah` = `min(total_cost)` subject to AKG lower bounds and the user budget. Pure LP relaxation viable since gram variables are continuous.
- `Paling Seimbang` = `min(total_cost + α · sum(slack_i))` with slack variables `slack_i ≥ AKG_i − achieved_i`, `slack_i ≥ 0`. Single-objective weighted sum, still a pure LP.
- `Paling Beragam` is **not a separate ILP**. We start from the `Termurah` plan and run a deterministic iterative-substitution heuristic: at each step, identify the ingredient with the lowest "nutrient density per rupiah" (an ingredient contributing little nutrient mass per cost), then attempt to swap a portion of it for an ingredient from a TKPI food group not yet present in the plan, requiring AKG bounds remain satisfied and budget not exceeded. Repeat until `count_groups ≥ count_groups(Termurah) + 2`, or until no feasible swap exists. If the target cannot be reached, the plan is returned with `diverse_constraint_relaxed: true` and a reason.

**Rationale**: The original Big-M food-group indicator MILP would add ~20 binary variables and ~40 linking constraints per solve, plus debug time on Big-M tightness. The heuristic is **deterministic** (canonical ordering, fixed tie-breaks), runs in a few hundred milliseconds even on the full catalog, and produces visibly different plans for the demo. We document in the README that `Paling Beragam` is heuristic-derived and explicitly call out the relaxation flag when it triggers — this is honest and shippable.

**Alternatives considered**: Big-M food-group indicator MILP (rejected: debug cost ≥ 2h), lexicographic max-min on adequacy ratios (rejected: hard to explain in 30 seconds of demo), full epsilon-constraint Pareto sweep (rejected: time).

### Decision 3: Sensitivity analysis via re-solve, not via duality

**Choice**: The "cabai +50%" / "telur −10%" / budget-slider features re-run the entire ILP with mutated price inputs. Target solve time <500ms keeps the slider feeling live.

**Rationale**: LP duality / shadow prices break across integer-influenced choices and are unintelligible in a demo. A re-solve is honest, deterministic, and visibly responsive.

### Decision 4: LLM humanizer is optional and gated; templated rendering is the required path

**Choice**: The required and default rendering is a deterministic templated Bahasa Indonesia recipe per meal slot, parameterized by ingredient and grams. The LLM upgrade calls the user's gateway, validates the LLM output by re-extracting ingredient grams from the rendered text and comparing against the source plan; on >5% drift or any missing ingredient, the system falls back to templated rendering.

**Rationale**: The templated rendering is what we ship to the demo. The LLM upgrade is a stretch goal that, when it works, looks impressive and natural; when it fails, the system stays correct. This protects the demo from any gateway flakiness.

**Alternatives considered**: LLM-only rendering (rejected: hallucination risk during live demo). Templated-only (acceptable; we explicitly claim "deterministic by design" if the LLM is dropped).

### Decision 5: Vite + React + Tailwind, not Next.js, not Streamlit

**Choice**: `apps/web/` is a Vite + React 18 + Tailwind 3 single-page app using shadcn-style copy-paste components and Recharts for the AKG bars. No SSR. Static build is served by nginx on the same VPS.

**Rationale**: Vite + React with copy-paste shadcn components is the fastest path to a polished UI a solo dev can ship in ~4 hours. Next.js adds SSR, App Router, and dependency surface we do not need. Streamlit ships in 1.5h but the demo video aesthetic suffers, and Design & UX is part of the rubric.

### Decision 6: Postgres on the VPS for plan caching only — no pgvector, no embeddings

**Choice**: A single table `plans(plan_hash PRIMARY KEY, request_json JSONB, response_json JSONB, created_at TIMESTAMPTZ DEFAULT now())`. Substitution suggestions come from a hand-curated `data/substitutes.yaml` covering the 30 most-common Indonesian ingredient swaps, indexed by `ingredient_id`.

**Rationale**: Plan caching gives idempotent demo behavior and protects judges who hit the live demo from cold-start latency. pgvector embeddings cost 3-4 hours to build (model download, embedding script, schema, query) for marginal demo benefit. A YAML table built in 30 minutes is enough.

**Alternatives considered**: SQLite (rejected at user's request — they have Postgres set up on the VPS already). pgvector (rejected on time). DuckDB (no benefit here).

### Decision 7: Two demo personas, no static fallback file

**Choice**: The front-end ships two demo personas: `Keluarga Bu Sari (4 anggota, Rp 60k/hari, DKI Jakarta)` for the feasible-flow demo, and `Anggaran Ekstrem (5 anggota, Rp 25k/hari, national-baseline)` for the infeasibility demo. Selecting a persona populates the form and runs the live optimizer. No precomputed JSON fallback is shipped.

**Rationale**: Two personas cover both demo branches in the video. Three more personas were planned originally but cost UX time (form variations) for diminishing video time. The static fallback was budgeted at ~2h; we drop it because the live demo on our own VPS during a recorded video is reliable enough — and the video is the canonical artifact regardless.

### Decision 8: Demo-first README and video script live in the repo

**Choice**: The repo contains `README.md` (judge-readable, mapped to the rubric) and `docs/demo-script.md` (a 3-minute video shot list with voiceover lines).

**Rationale**: Judges spend ≤5 minutes per submission. Optimize for skim. The README is part of the product surface, not an afterthought.

### Decision 9: TKPI sourced from `panganku.org` HTML scrape, not the PDF book

**Choice**: `services/api/scripts/scrape_panganku.py` performs an authenticated-GET-only scrape of `https://www.panganku.org/id-ID/semua_nutrisi`, persists raw HTML pages under `data/raw/panganku/<slug>.html`, then parses them into `data/normalized/ingredients.json`. The scrape is one-shot, committed to the repo, and not re-run during deployment.

**Rationale**: TKPI is officially published as a 140-page PDF (ISBN 978-623-301-0368) which is impractical to parse in a hackathon timeframe. The same dataset is rendered as HTML tables on `panganku.org`, the official Kemenkes-affiliated portal. Scraping HTML is bounded (~1500 ingredients, ~30 minutes wall-clock with 1-second polite delay between requests) and deterministic. We credit the Kemenkes TKPI book as the upstream regulatory source in `data/MANIFEST.md` while citing `panganku.org` as the technical retrieval channel.

**Alternatives considered**: Parsing the PDF (`pdfplumber` + table heuristics — rejected: 4-6h plus uncertain accuracy on a multi-column nutrient table). Using `eriko-syah/indonesian-food` Hugging Face dataset (1350 rows, missing iron/zinc/vitamin A — insufficient for our 8 tracked nutrients). Using FAO/INFOODS Indonesia table (less granular, missing many local ingredients).

### Decision 10: Cooking-method mapping is a hand-curated YAML, not learned

**Choice**: `data/cooking-method.yaml` maps each TKPI ingredient (or food group as a fallback) to one preferred cooking verb from the fixed vocabulary (`tumis`, `rebus`, `kukus`, `goreng`, `sangrai`). The templated humanizer reads this file to choose the right verb; if the ingredient is missing from the file, the food-group fallback is used.

**Rationale**: Choosing a cooking method is a simple deterministic lookup. Letting the LLM decide it would re-introduce non-determinism and a validation surface. A hand-curated YAML covering the ~60 most common ingredients takes 20 minutes and is explainable to a judge in one sentence.

### Decision 11: Loading and error states are first-class UI surfaces

**Choice**: The front-end ships skeleton states for the plan cards (during `/v1/optimize` solve, 500-1500ms), an error toast for any non-2xx API response, and an empty-initial-state hero card explaining the product when no inputs have been entered yet. The "Mode Demo Offline" banner is dropped (we removed the static fallback in Decision 7 above) and replaced by a clearer "API tidak tersedia" error toast with a retry button.

**Rationale**: The 3-minute demo video will pause on these states. They cannot look broken or generic. ~30 minutes of additional UI work for materially better demo polish.

## Risks / Trade-offs

- **Risk**: TKPI is distributed primarily as a 140-page PDF book; CSV form is not officially published. → **Mitigation**: We scrape the official Kemenkes web portal `panganku.org/id-ID/semua_nutrisi` which renders the same dataset in HTML tables. Scraper output is committed under `data/raw/panganku/` for reproducibility, and we credit Kemenkes / panganku.org as the canonical source. Budget: ~1h scrape + 30min normalize.

- **Risk**: ILP infeasibility at low budgets is common (Rp 10k/day cannot meet AKG for a family of 5). → **Mitigation**: Infeasibility is a feature, not a bug. We surface it with a UI panel ("Plan tidak feasible — minimum Rp X/hari untuk memenuhi AKG zat besi") and a one-click "Naikkan budget" action. This is one of the strongest demo beats.
- **Risk**: AKG normative source confusion (Permenkes 28/2019 vs. older 75/2013). → **Mitigation**: Lock to Permenkes 28/2019, cite in README, store as versioned JSON.
- **Risk**: TKPI dataset inconsistency (units, missing values). → **Mitigation**: A normalizer asserts unit consistency, drops malformed rows, logs them under `data/validation-report.json`. Budgeted at ~1.5h.
- **Risk**: LLM gateway returns drift or missing ingredients. → **Mitigation**: Validator compares humanized portions to source plan; >5% drift triggers templated fallback. Logged in response metadata.
- **Risk**: Solver time >500ms on slider re-solve breaks the "live math" feel. → **Mitigation**: We pre-warm the CBC solver in a long-lived FastAPI worker and rely on the small problem size.
- **Risk**: Solo developer fatigue around hour 24. → **Mitigation**: Strict cut-line rules in tasks.md — anything tagged `[CUTLINE]` drops without guilt.
- **Risk**: Live demo on VPS goes down during judging. → **Mitigation**: The 3-minute video is the canonical artifact. Live demo is a bonus. Plan caching ensures the demo personas hit warm responses.
- **Risk**: Gateway model `gpt-5.4-mini` returns different JSON shape than expected. → **Mitigation**: We use plain text completion for humanization, not structured output, and parse with regex tolerant of light variation. Fallback to templated on parse failure.
- **Trade-off**: Choosing ILP over RL/heuristic loses some "AI buzz" but wins the "honest algorithm" narrative. We lean into this in the README.
- **Trade-off**: Bahasa Indonesia only narrows the English-speaking judge experience. Mitigated by English subtitles in the demo video and an English-language README.
