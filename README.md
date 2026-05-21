# GiziGo

> **Operations-research-grade meal planner against Indonesian childhood stunting.**
> Submitted to ALGOfest Hackathon 2026 (Battle of the Beasts).
>
> 🌐 Live demo: **https://gizigo.jmola.my.id**

![GiziGo plan cards](docs/screenshots/02-bu-sari-success.png)

GiziGo turns every Rupiah of household food budget into the *most nutritious* daily meal plan it can buy. The user enters the family composition (toddlers, school children, lactating mothers, etc.), a daily budget, region, and any dietary restrictions. In under a second the service returns three optimal plans (Cheapest / Most Balanced / Most Varied), each with a per-nutrient AKG achievement bar, a sensitivity-analysis slider, and an infeasibility coach when the budget cannot meet the family's nutritional minimums.

The work is grounded in two government data sources:

- **Tabel Komposisi Pangan Indonesia 2020** (Direktorat Gizi Masyarakat, Kemenkes RI) — 1,146 ingredients with eight tracked nutrients each.
- **Permenkes 28/2019** — the Angka Kecukupan Gizi standard for seven AKG categories that cover both demo personas.

## Why this matters

Indonesia's under-five stunting rate is **21.6 % (SSGI 2024)** while the RPJMN 2024-2029 target is 14 %. Stunting is rooted in the first 1,000 days of life, where the limiting factor is most often *cost-feasible nutrition*, not knowledge. GiziGo attacks that gap directly: it answers *"given my budget today, what is the most nutritious mix of cheap local foods I can buy?"* — and tells the user exactly when the budget falls short and by how much.

## What's inside

```
              ┌──────────────────────────────────────────────────┐
              │  apps/web (Vite + React + Tailwind)              │
              │   • HouseholdForm + persona menu                 │
              │   • PlanCard with 8 AKG achievement bars         │
              │   • SensitivityBar (debounced re-solve)          │
              │   • InfeasibilityPanel + RecipeDrawer            │
              └──────────────────┬───────────────────────────────┘
                                 │ HTTPS, JSON, CORS
              ┌──────────────────▼───────────────────────────────┐
              │  services/api (FastAPI on uvicorn)               │
              │   • /v1/optimize  – ILP solve (PuLP + CBC)       │
              │   • /v1/sensitivity – full re-solve under price  │
              │     perturbations (~120 ms typical)              │
              │   • /v1/humanize   – templated meal narration    │
              │   • /v1/health     – catalog + DB liveness       │
              └──────────────────┬───────────────────────────────┘
                                 │ asyncpg
              ┌──────────────────▼───────────────────────────────┐
              │  Postgres 16 (plan caching, idempotent on hash)  │
              └──────────────────────────────────────────────────┘
```

The optimizer is a **deterministic linear program**, not a chatbot. We chose the ILP route because the problem itself is mathematically clean: minimize cost subject to AKG floor constraints, a budget cap, hard exclusions for restrictions, and per-ingredient gram caps. Three plans are produced from this base:

| Plan | Objective | Method |
|---|---|---|
| **Cheapest** | `min Σ price·grams` | Pure cost LP |
| **Most Balanced** | `min Σ (price·grams) + 50 · Σ slack_n` | Weighted-sum LP with slack ≥ AKG_n − achieved_n |
| **Most Varied** | Maximise distinct food groups while staying near optimal | Iterative-substitution heuristic on top of *Cheapest* |

When no feasible solution exists at the user's budget, GiziGo runs a **bisection search on the budget** to estimate the *minimum feasible budget*, then reports the deficit nutrients and offers a one-click "raise to minimum" action — turning a frustrating "no answer" into actionable guidance.

![Infeasibility panel](docs/screenshots/03-infeasibility.png)

A full system architecture diagram lives at [`docs/architecture.svg`](docs/architecture.svg).

A full mathematical formulation lives in [`docs/ilp-formulation.md`](docs/ilp-formulation.md). Sensitivity analysis is implemented as full re-solves rather than dual variables, which keeps the code small and the latency under 500 ms while still being honest about how prices and AKGs interact.

## Submitted under

| Track | How GiziGo fits |
|---|---|
| **Best HealthTech Project** | Direct attack on stunting via personalized AKG planning grounded in Permenkes 28/2019 |
| **Best Social Impact** | Targets a 21.6 % national stunting rate; UI in English with two demo personas anchored in real Indonesian household profiles |
| **Top 3 Grand** | Operations-research depth (ILP + sensitivity + bisection) plus a polished, end-to-end live deployment |

## Two demo personas

1. **Bu Sari's Family** — father (19-49), Bu Sari (lactating mother), child 5 yrs, toddler. Rp 60,000/day, region DKI Jakarta. Optimizer returns ~Rp 35,000 across 5+ food groups, all eight AKG nutrients ≥ 100 %.
2. **Extreme Budget** — 5-member household, region National Median, Rp 25,000/day. Optimizer returns *infeasible*, surfaces the minimum estimated budget at Rp 41,000-63,000 (depending on persona shape), and lists the deficit nutrients (energy, protein, vitamin A, calcium).

Both personas are baked into the UI as one-click chips so the judge can reproduce them in 2 seconds. They also have **deep-link URLs** that auto-load and auto-calculate:

- https://gizigo.jmola.my.id/?persona=bu_sari
- https://gizigo.jmola.my.id/?persona=anggaran_ekstrem

Each plan card has a **print button** that renders a single-page A4 PDF of just that plan (header, AKG bars, full ingredient list grouped by meal slot) using the browser's built-in print engine — useful for handing to a community-health worker or printing as a fridge reminder.

## Technologies used

- **Backend**: Python 3.10+, FastAPI 0.136, PuLP 3.3 (CBC), Pydantic v2, asyncpg, BeautifulSoup4
- **Frontend**: Vite 8, React 18, Tailwind 3, Recharts, Zod, Sonner, Lucide
- **Data**: Postgres 16 (plan cache, JSONB), one-shot scrape of panganku.org committed under `data/raw/panganku/`
- **Infra**: Ubuntu 22.04 VPS, Docker, nginx, Let's Encrypt via certbot, systemd

## Reproducibility

```bash
make bootstrap       # creates Python venv, installs web deps, starts local Postgres
make data            # idempotent scrape + normalize (1146 ingredients, 0 errors)
make api-dev         # starts FastAPI on :8001 (with --reload)
make web-dev         # starts Vite on :5173
make test            # pytest unit tests
make deploy          # rsync + remote bootstrap (uses SSH alias `vpsgw`)
```

Every dataset is committed to the repo so the build is reproducible without re-hitting upstream sources. See [`data/MANIFEST.md`](data/MANIFEST.md) for the full provenance.

## Repository layout

```
.
├── services/api/          FastAPI service (Python 3.10)
│   ├── src/               models, optimizer, humanizer, main
│   ├── scripts/           one-shot scrape + normalize
│   └── tests/
├── apps/web/              Vite React app
├── data/
│   ├── raw/panganku/      ~1146 raw HTML detail pages, committed
│   ├── normalized/        ingredients.json, food_groups.json
│   ├── akg/               permenkes-28-2019.json (7 AKG categories)
│   ├── prices/            dki_jakarta.yaml + national_baseline.yaml
│   ├── substitutes.yaml
│   └── cooking-method.yaml
├── docs/
│   ├── ilp-formulation.md
│   ├── data-sources.md
│   └── demo-script.md
├── openspec/changes/gizigo-meal-optimizer/  full spec-driven design trail
├── scripts/               deploy.sh, docker-postgres.sh, nginx + systemd templates
└── Makefile
```

## Limitations and honest disclosure

- The price tables are a **manually curated 68-ingredient subset** sampled May 2026 from infopangan.jakarta.go.id and PIHPS Bank Indonesia. The optimizer would scale to the full 1,146-ingredient catalog as soon as more prices are filled in.
- The cooking-method humanizer is **template-driven** by default. An optional LLM path exists behind the `HUMANIZER_LLM_ENABLED` flag with a post-render validator that re-extracts ingredient grams; if drift > 5 %, the LLM output is discarded and the templated path is used. The default is off so the demo stays deterministic.
- The "Most Varied" plan is a deterministic iterative-substitution heuristic on top of "Cheapest", not a separate ILP. When the variety target cannot be reached without violating AKG or budget, the plan is flagged with a `diverse_constraint_relaxed` badge and the reason is shown to the user.

## Credits

- TKPI 2020: ISBN 978-623-301-0368 — Kemenkes RI, retrieved via panganku.org.
- Permenkes 28/2019: Peraturan Menteri Kesehatan RI No. 28 Tahun 2019.
- Solver: COIN-OR CBC (Eclipse Public License) via PuLP (MIT).
- All code original to this hackathon.

## License

MIT. See [LICENSE](LICENSE).
