# GiziGo

> **Operations-research-grade meal planner against Indonesian childhood stunting.**
> Submitted to ALGOfest Hackathon 2026 (Battle of the Beasts).
>
> 🌐 Live demo: **https://gizigo.jmola.my.id**

![GiziGo plan cards](docs/screenshots/02-bu-sari-success.png)

GiziGo turns every Rupiah of household food budget into the *most nutritious* daily meal plan it can buy. The user enters the family composition (toddlers, school children, lactating mothers, etc.), a daily budget, region, and any dietary restrictions. In under a second the service returns three optimal plans (Cheapest / Most Balanced / Most Varied), each with a per-nutrient AKG achievement bar, a sensitivity-analysis slider, and an infeasibility coach when the budget cannot meet the family's nutritional minimums.

The work is grounded in two government data sources:

- **Tabel Komposisi Pangan Indonesia 2020** (Direktorat Gizi Masyarakat, Kemenkes RI) — 1,146 ingredients with nine tracked nutrients each (energy, protein, fat, carbohydrate, **fiber**, iron, zinc, vitamin A, calcium).
- **Permenkes 28/2019** — the Angka Kecukupan Gizi standard for seven AKG categories that cover both demo personas.

## Why this matters

Indonesia's under-five stunting rate is **19.8% (SSGI 2024)** while the RPJMN 2024-2029 target is 14 %. Stunting is rooted in the first 1,000 days of life, where the limiting factor is most often *cost-feasible nutrition*, not knowledge. GiziGo attacks that gap directly: it answers *"given my budget today, what is the most nutritious mix of cheap local foods I can buy?"* — and tells the user exactly when the budget falls short and by how much.

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
| **Most Balanced** | `min Σ (price·grams) + α · max_n overshoot_n` | LP with over-shoot variables capped at 1.3 × RDA per nutrient |
| **Most Varied** | `max Σ binary food_group_present` | MIP with binary group-presence indicators, ≤ 1.05× cheapest cost |

When no feasible solution exists at the user's budget, GiziGo runs a **bisection search on the budget** to estimate the *minimum feasible budget*, then reports the deficit nutrients and offers a one-click "raise to minimum" action — turning a frustrating "no answer" into actionable guidance.

![Infeasibility panel](docs/screenshots/03-infeasibility.png)

A full system architecture diagram lives at [`docs/architecture.svg`](docs/architecture.svg).

A full mathematical formulation lives in [`docs/ilp-formulation.md`](docs/ilp-formulation.md). Sensitivity analysis is implemented as full re-solves rather than dual variables, which keeps the code small and the latency under 500 ms while still being honest about how prices and AKGs interact.

## Submitted under

| Track | How GiziGo fits |
|---|---|
| **Best HealthTech Project** | Direct attack on stunting via personalized AKG planning grounded in Permenkes 28/2019. Provides an audit layer for the *Makan Bergizi Gratis* (MBG) program. |
| **Best Social Impact** | Targets a 19.8% national stunting rate; UI in English with three demo personas anchored in real Indonesian household and program-operator profiles |
| **Top 3 Grand** | Operations-research depth (ILP + sensitivity + bisection) plus a polished, end-to-end live deployment with concrete policy relevance to a Rp 71-trillion national program |

## Four demo personas

1. **Bu Sari's Family** — father (19-49), Bu Sari (lactating mother), child 5 yrs, toddler. Rp 65,000/day, DKI Jakarta. Three differentiated plans: cheapest Rp 60,534 / balanced Rp 65,000 / diverse Rp 63,560 (11 food groups, 12 ingredients). All 9 AKG nutrients ≥ 100%.
2. **Extreme Budget** — 5-member household, National Median, Rp 25,000/day. Infeasible — minimum Rp 68,000, deficits: energy, protein, vitamin A, calcium.
3. **MBG SPPG — NTT** — one primary-school student, Rp 9,500/day, **Nusa Tenggara Timur** (stunting 37.2%, prices 18% above national median due to logistics). **Infeasible** — minimum Rp 11,000. This is the key policy finding: the Rp 10k MBG envelope is *not sufficient* in Indonesia's highest-stunting province.
4. **SPPG Operator** — one representative student, Rp 1,000,000/day (= Rp 10k × 100 portions). Models a BGN SPPG kitchen procuring for 100 students. Cheapest plan Rp 9,872/student — Rp 128 headroom from the Rp 10k envelope.

All four personas are one-click chips with **deep-link URLs** that auto-load and auto-calculate:

- https://gizigo.jmola.my.id/?persona=bu_sari
- https://gizigo.jmola.my.id/?persona=anggaran_ekstrem
- https://gizigo.jmola.my.id/?persona=mbg_sppg
- https://gizigo.jmola.my.id/?persona=sppg_operator

## Policy implication: Makan Bergizi Gratis (MBG) + Province Inequality

The MBG program (Perpres 83/2024, Rp 71T budget) targets ~82.9 million beneficiaries by 2029 with a per-portion budget of **Rp 10,000-15,000**. Public debate has questioned whether that envelope is sufficient.

GiziGo answers this with two lenses:

**National median**: At Rp 9,872/student, the cheapest AKG-compliant plan leaves only Rp 128-3,000 headroom from the Rp 10-12k envelope. Feasible — but barely.

**NTT (stunting 37.2%, prices ×1.18)**: At Rp 9,500/student, the LP is **infeasible**. Minimum feasible budget: Rp 11,000. The MBG envelope of Rp 10k is not sufficient in Indonesia's highest-stunting province. The optimizer surfaces exactly which nutrients are short and by how much.

**Price shock sensitivity**: Click "Chili +120% (Natal 2025)" — the actual peak price recorded in December 2025 (Rp 80-90k/kg). The LP re-solves in 100ms and shows the new cost. Click "Rice +15% (El Niño)" to model a drought scenario. These are not linear extrapolations — they are actual re-optimisations.

**7 regions available**: DKI Jakarta, National Median, Jawa Barat (24.5%), Jawa Tengah (20.8%), Jawa Timur (19.2%), Sumatera Utara (25.8%), NTT (37.2%). Each region has its own price table reflecting logistics and distribution costs. The stunting rate is shown on each region button so the user understands the context.

| Plan | Cost (NTT) | Cost (National) | Δ |
|---|---|---|---|
| Cheapest | Infeasible at Rp 9.5k | Rp 9,872 | — |
| Most Balanced | Infeasible at Rp 9.5k | Rp 11,290 | — |
| Most Varied | Infeasible at Rp 9.5k | Rp 10,366 | — |

**The headline finding**: the MBG budget is sufficient at national-median prices but fails in NTT — Indonesia's province with the highest stunting rate. GiziGo is the audit layer that catches this before the kitchen does.
- Plug in the budget envelope and let the optimizer return the cheapest AKG-compliant ingredient mix.
- Use the sensitivity slider to plan against price shocks (chili, eggs, beef) before they hit operations.

This is not an attack on the program. It's the audit layer the program needs.

Each plan card has a **print button** that renders a single-page A4 PDF of just that plan (header, AKG bars, full ingredient list grouped by meal slot) using the browser's built-in print engine — useful for handing to a community-health worker, a teacher, or printing as an SPPG kitchen-prep sheet.

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
│   ├── akg/               permenkes-28-2019.json (14 AKG categories × 9 nutrients)
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

- The price tables are a **manually curated 105-ingredient subset** sampled May 2026 from infopangan.jakarta.go.id and PIHPS Bank Indonesia. The optimizer would scale to the full 1,146-ingredient catalog as soon as more prices are filled in.
- The cooking-method humanizer is **template-driven** by default. An optional LLM path exists behind the `HUMANIZER_LLM_ENABLED` flag with a post-render validator that re-extracts ingredient grams; if drift > 5 %, the LLM output is discarded and the templated path is used. The default is off so the demo stays deterministic.
- The "Most Varied" plan is a deterministic iterative-substitution heuristic on top of "Cheapest", not a separate ILP. When the variety target cannot be reached without violating AKG or budget, the plan is flagged with a `diverse_constraint_relaxed` badge and the reason is shown to the user.

## Credits

- TKPI 2020: ISBN 978-623-301-0368 — Kemenkes RI, retrieved via panganku.org.
- Permenkes 28/2019: Peraturan Menteri Kesehatan RI No. 28 Tahun 2019.
- Solver: COIN-OR CBC (Eclipse Public License) via PuLP (MIT).
- All code original to this hackathon.

## License

MIT. See [LICENSE](LICENSE).
