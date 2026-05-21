# ILP Formulation

GiziGo's optimizer is a deterministic linear program solved by COIN-OR CBC via PuLP. This document writes out the model the way an Operations Research practitioner would.

## Notation

| Symbol | Meaning |
|---|---|
| $I$ | Set of eligible ingredients (those priced for the chosen region and not excluded by restrictions) |
| $N$ | Set of tracked nutrients (8 of them: energy_kcal, protein_g, fat_g, carbohydrate_g, iron_mg, zinc_mg, vitamin_a_ug_rae, calcium_mg) |
| $g_i$ | Decision variable, grams of ingredient $i$ to include in the daily plan ($g_i \ge 0$) |
| $p_i$ | Price of ingredient $i$ per 100 g, in IDR |
| $a_{i,n}$ | Nutrient $n$ in ingredient $i$, per 100 g (units match the nutrient: kcal, g, mg, µg RAE) |
| $R_n$ | Required AKG floor for nutrient $n$, summed over the household |
| $B$ | Daily budget, in IDR |
| $G_{\max}$ | Per-ingredient gram cap (1500 g) — prevents trivial single-ingredient solutions |
| $\alpha$ | Slack penalty weight for the balanced LP (default 50) |

## The household requirement vector

For a household with members $H$, the required nutrient floor is

$$
R_n = \sum_{m \in H} \mathrm{AKG}_n(m)
$$

where $\mathrm{AKG}_n(m)$ is the value from `data/akg/permenkes-28-2019.json` for member $m$'s AKG category and nutrient $n$. The lactating-mother category already includes the 0-6 month supplement applied to the adult-female baseline.

## Plan 1 — *Termurah* (Pure cost LP)

$$
\begin{aligned}
\min_{g} & \quad \sum_{i \in I} \frac{p_i}{100} \cdot g_i \\
\text{s.t.} & \quad \sum_{i \in I} \frac{a_{i,n}}{100} \cdot g_i \ge R_n & & \forall n \in N \\
& \quad \sum_{i \in I} \frac{p_i}{100} \cdot g_i \le B \\
& \quad 0 \le g_i \le G_{\max} & & \forall i \in I
\end{aligned}
$$

If this LP is infeasible (no allocation satisfies AKG within budget) we fall through to the infeasibility analyzer.

## Plan 2 — *Paling Seimbang* (Cost + AKG slack)

$$
\begin{aligned}
\min_{g, s} & \quad \sum_{i \in I} \frac{p_i}{100} g_i + \alpha \sum_{n \in N} s_n \\
\text{s.t.} & \quad \sum_{i \in I} \frac{a_{i,n}}{100} g_i + s_n \ge R_n & & \forall n \in N \\
& \quad s_n \ge 0 & & \forall n \in N \\
& \quad \sum_{i \in I} \frac{p_i}{100} g_i \le B \\
& \quad 0 \le g_i \le G_{\max} & & \forall i \in I
\end{aligned}
$$

Slack variables $s_n$ allow controlled under-fulfillment when the AKG cannot be met cheaply, but the penalty $\alpha = 50$ makes the solver pay heavily for any slack — in practice slack only appears under genuine deficit conditions, and it is then mirrored into the achievement percentages shown in the UI.

## Plan 3 — *Paling Beragam* (Heuristic on top of Termurah)

This is **not** a separate ILP. It runs as a deterministic iterative-substitution heuristic:

1. Start from the *Termurah* solution $g^\star$.
2. Identify the set of food groups $G_\star$ that already appear (≥ 10 g threshold).
3. Pick a candidate "donor" ingredient — the one with the lowest *nutrient-density-per-Rupiah* among already-used groups.
4. Pick a candidate "acceptor" — the cheapest ingredient from a previously unused food group.
5. Reallocate the donor's spend to the acceptor. Recompute achievement and cost.
6. Reject the swap if either (a) total cost exceeds budget, or (b) any AKG drops below 95 % of the floor.
7. Repeat for at most two new groups.

If a swap fails the heuristic emits `diverse_constraint_relaxed: true` with reason `budget_exhausted` or `akg_bound_violated`. The UI surfaces this as an honest amber badge — the system never lies that diversification "succeeded" when it didn't.

## Sensitivity analysis

GiziGo implements sensitivity by **full ILP re-solve** under perturbed prices, not via dual variables. The perturbation request looks like

```json
{ "perturbations": [{"ingredient_id": "tkpi_NR014", "delta_pct": 50}] }
```

Each perturbation $\delta_i$ multiplies the price: $p_i' = p_i (1 + \delta_i / 100)$. The cost LP is re-run and the *cost delta* is reported. Latency stays under 500 ms on the demo personas.

We chose re-solve over dual variables because (a) constraint shadows can change discretely once the basis flips, so duals are not safe extrapolators across large perturbations; (b) the LP is small and CBC solves Termurah from scratch in ~30-100 ms; (c) the UI is honest about *the actual new optimal*, not a linear approximation.

## Infeasibility analyzer

When *Termurah* returns infeasible at the user's budget, GiziGo runs a **bisection on the budget**:

1. Try the current budget × 100 as the upper bound. If still infeasible, the deficit is structural (restrictions are too strict) — return `INFEASIBLE_RESTRICTIONS`.
2. Otherwise bisect between 0 and 100× until the gap is below max(Rp 1.000, current_budget / 100).
3. Round the resulting minimum up to the nearest Rp 1.000 and surface it as `minimum_feasible_budget_idr`, together with the list of nutrients that were short.

This is what powers the "Naikkan ke anggaran minimum" CTA in the InfeasibilityPanel — the user gets a one-tap path from frustration to a working plan.

## Determinism

Because the demo must reproduce identically every time, the CBC solver is configured with:

- `threads=1` — no nondeterministic interleaving across cores
- `randomS 1` — fixed branch-and-bound random seed
- `presolve=on, cuts=off` — keep the search tree shallow and predictable
- `PYTHONHASHSEED=0` — Python set/dict iteration order frozen

Plan responses are also content-addressed by a SHA-256 `plan_hash` over the canonicalised request (members + budget + region + restrictions + plan_types + catalog_hash), and cached in Postgres `plans(plan_hash, request_json, response_json)`. This means repeat clicks return in single-digit milliseconds.

## Why ILP over heuristics or LLMs

Three reasons make ILP the right tool here:

1. **Provable optimality.** "I will give you the cheapest plan that meets your nutritional floor" is a *promise* that LLMs cannot honour and metaheuristics can only approximate. A linear program either finds the global optimum or proves none exists.
2. **Exact infeasibility.** When the budget is too low, an LP tells you exactly which constraint binds and how far you are from feasibility. Bisection on the budget then maps that back to a Rupiah figure for the user.
3. **Latency budget.** A small LP is solved in tens of milliseconds. The user experience stays interactive — the slider can drive a real re-solve on every release event without a spinner.

The cost is calibration honesty: input data quality is the entire ballgame. We invested in that side (one-shot scrape of TKPI, AKG straight from the Permenkes, hand-vetted retail prices) and kept the solver simple and exact.
