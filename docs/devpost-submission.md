# Devpost submission body

Paste these fields directly into https://algofest-hackathon2.devpost.com/submissions/new

---

## Project name

**GiziGo — Operations-research meal planner against childhood stunting**

## Tagline (≤ 200 chars)

Turn every Rupiah into the most nutritious daily plate. ILP-grade meal optimisation for Indonesian families against the 21.6 % under-five stunting rate.

## Elevator pitch (long description)

Indonesia's under-five stunting rate is **21.6 %** while the RPJMN 2024-2029 target is 14 %. The gap is rarely about knowledge — it's about turning a tight household budget into nutritionally sufficient meals on a given day, in a given region.

**GiziGo answers that exact question** with the discipline of an Operations Research solver. Enter your family composition (toddler, school child, lactating mother, etc.), a daily budget, your region, and any dietary restrictions. Within a second, the system returns three optimal plans:

- **Cheapest** — pure cost minimisation under all eight tracked AKG nutrients.
- **Most Balanced** — cost plus a slack penalty so AKGs are met as evenly as possible.
- **Most Varied** — an iterative-substitution heuristic that maximises distinct food groups while staying near optimal.

When the budget cannot meet AKG, GiziGo runs a **bisection search on the budget** to surface the *minimum feasible budget* and the nutrient deficits, with a single CTA that raises to the minimum and re-runs the optimiser. A **sensitivity-analysis slider** re-solves the LP under perturbed prices in real time — slide chili up 50 %, watch the *actual new optimum* (not a linear extrapolation) appear.

The UI is in Bahasa Indonesia for the people it's actually for; the architecture, code, and README are in English for the judges. The 1,146-ingredient nutrient catalogue comes from an idempotent scrape of panganku.org (the Kemenkes-affiliated re-publisher of TKPI 2020). AKG values come from Permenkes 28/2019. Retail prices come from infopangan.jakarta.go.id and PIHPS Bank Indonesia. Everything is committed to the repo for reproducibility — `make data` re-builds the entire dataset.

## What it does

1. Take a household composition + daily budget + region + restrictions.
2. Run a deterministic linear program (PuLP + COIN-OR CBC) to find the cheapest meal mix that meets the household's summed AKG floor.
3. Run a second LP with slack variables to find the most balanced plan.
4. Apply a deterministic iterative-substitution heuristic to find the most varied plan that's still nutritionally and budget-feasible.
5. If infeasible, bisect on the budget to surface the minimum feasible Rupiah amount and the deficit nutrient list.
6. Render every plan as recipe-style narration via a hand-curated cooking-method map, organised by sarapan / makan siang / makan malam / kudapan.
7. Let the user perturb prices and watch the optimiser re-solve in under 500 ms.

## How we built it

- **ILP modeling** in PuLP (MIT) on top of the COIN-OR CBC solver (EPL). The model is documented at `docs/ilp-formulation.md`.
- **FastAPI** for the HTTP surface, with strict Pydantic v2 schemas and content-addressed plan caching in **Postgres** (`plans(plan_hash, request_json, response_json)`).
- **Vite + React 18 + Tailwind 3** for the front-end; **Recharts** for the AKG bars; **Sonner** for toast notifications; **Zod** for client-side validation that mirrors the Pydantic schemas.
- **Postgres 16 in Docker** on the VPS, bound to localhost.
- **systemd + nginx + Let's Encrypt** for the deployment. TLS issued via certbot http-01 webroot.
- One-shot scrape of **panganku.org** (1,146 detail pages, polite 0.3 s delay), normalised to JSON, validated, hashed.

## Challenges we ran into

- **Single-developer 36-hour timeline** forced cuts: pgvector embeddings dropped in favour of hand-curated substitution YAML; Next.js dropped in favour of Vite for faster ship; LLM humanizer demoted to optional behind a feature flag.
- **TKPI scraping**: the Kemenkes data is published as a paginated HTML detail-page-per-ingredient set. We wrote an idempotent scraper that respects rate limits and committed every raw HTML to the repo for reproducibility.
- **Determinism**: CBC's branch-and-bound has random tie-breaking. We pinned `randomS=1`, `threads=1`, `presolve=on`, `cuts=off`, and `PYTHONHASHSEED=0` so the demo replays bit-for-bit.
- **Postgres password sync** after the VPS provisioning, because the initial container persisted across `deploy.sh` re-runs while a fresh `.env` was generated. Resolved by `ALTER USER` from the deploy script.

## Accomplishments we're proud of

- A real linear program — not a chatbot wrapper. The solver either gives the global optimum or proves none exists.
- An **honest infeasibility experience** with a one-click "raise budget to minimum" action.
- Sub-second sensitivity by full re-solve, not approximation.
- Full reproducibility: `make data` rebuilds the entire dataset from committed sources.
- Live deployment with valid HTTPS at https://gizigo.jmola.my.id.

## What we learned

- LP relaxations are surprisingly expressive for nutrition problems — slack-penalised LPs solve the "balanced plan" pain point without any new modelling vocabulary.
- Operations Research **is** demo-friendly when you build the right UI around it. The sensitivity slider sells the math better than any explanation.
- Determinism is a feature, not an accident.

## What's next

- Expand the price-table coverage from 40 to all 1,146 ingredients via a scheduled scrape of PIHPS regional data.
- Add a multi-day plan with leftover-aware constraints (a 3-day or weekly plan that minimises waste).
- Posyandu / Puskesmas integration for community health worker workflows.
- Mobile-first PWA wrapper for offline use in low-connectivity areas.

---

## Devpost form fields

| Field | Value |
|---|---|
| **Project name** | GiziGo |
| **Tagline** | Turn every Rupiah into the most nutritious daily plate. ILP-grade meal optimisation for Indonesian families against the 21.6 % under-five stunting rate. |
| **Image** | docs/screenshots/02-bu-sari-success.png |
| **Try it out link 1** | https://gizigo.jmola.my.id |
| **Try it out link 2** | (GitHub repo URL — paste once repo is public) |
| **Demo video link** | (YouTube unlisted URL — paste after upload) |
| **Categories** | HealthTech (primary), Open Innovation (secondary), Best Social Impact, AI/ML, Most Innovative |
| **Built with** | python, fastapi, pulp, coin-or-cbc, postgresql, react, vite, tailwindcss, recharts, zod, nginx, docker, lets-encrypt, ubuntu |
| **Team** | Solo |

## Pre-submission checklist

- [ ] Repo is public on GitHub
- [ ] README.md renders correctly on GitHub (relative image paths work)
- [ ] License file (MIT) committed
- [ ] `make data` and `make api-dev` and `make web-dev` all run on a fresh clone
- [ ] Live URL https://gizigo.jmola.my.id is up (HEAD 200, /v1/health returns ok=true)
- [ ] Demo video uploaded to YouTube as Unlisted
- [ ] Devpost project page completed and submitted
- [ ] Final review at T-2h: re-test the live URL once more before deadline
