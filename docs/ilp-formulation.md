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

## Plan 1 — *Cheapest* (Pure cost LP)

$$
\begin{aligned}
\min_{g} & \quad \sum_{i \in I} \frac{p_i}{100} \cdot g_i \\
\text{s.t.} & \quad \sum_{i \in I} \frac{a_{i,n}}{100} \cdot g_i \ge R_n & & \forall n \in N \\
& \quad \sum_{i \in I} \frac{p_i}{100} \cdot g_i \le B \\
& \quad 0 \le g_i \le G_{\max} & & \forall i \in I
\end{aligned}
$$

If this LP is infeasible (no allocation satisfies AKG within budget) we fall through to the infeasibility analyzer.

## Plan 2 — *Most Balanced* (Cost + max-overshoot penalty)

The previous design used slack variables on the AKG floor — but when the cheapest LP already meets every AKG perfectly, every slack is zero and the balanced LP collapses to the cheapest LP. That's mathematically correct but produces three identical plan cards. The reformulation below shifts the penalty from *under*-shoot to *over*-shoot, which is the actual problem cheapest plans have: they concentrate spend on one or two cheap-but-nutrient-dense ingredients and over-shoot iron / vitamin A by 200%+ while just clearing the floor on others.

$$
\begin{aligned}
\min_{g, o, M} & \quad \sum_{i \in I} \frac{p_i}{100} g_i + \alpha \cdot B \cdot M \\
\text{s.t.} & \quad \sum_{i \in I} \frac{a_{i,n}}{100} g_i \ge R_n & & \forall n \in N \\
& \quad \sum_{i \in I} \frac{a_{i,n}}{100} g_i - o_n \le \tau \cdot R_n & & \forall n \in N \\
& \quad o_n \le M \cdot R_n & & \forall n \in N \\
& \quad o_n, M \ge 0 \\
& \quad \sum_{i \in I} \frac{p_i}{100} g_i \le B \\
& \quad 0 \le g_i \le G_{\max} & & \forall i \in I
\end{aligned}
$$

where $\tau = 1.3$ (over-shoot threshold of 130% RDA), $\alpha = 2.0$ (penalty weight, scaled by budget so its magnitude is comparable to cost), $o_n$ is the over-shoot in nutrient $n$ above the threshold, and $M$ is the *maximum normalised over-shoot ratio* across all nutrients. Penalising the maximum (rather than the sum) prevents the solver from trading low overshoot in one nutrient against high overshoot in another — it pushes for a *flat* nutritional profile.

In practice on Bu Sari (Rp 60k DKI): cheapest gives iron 221%, balanced gives iron 185%, cost rises Rp 57,936 → Rp 60,000 (3.5% premium for nutritional smoothness).

## Plan 3 — *Most Varied* (Mixed-integer program on food groups)

This is now a **proper MIP**, not a heuristic. We add a binary indicator $x_g \in \{0, 1\}$ per food group $g \in G$ that is forced to 1 only if at least $\theta = 50$ g from that group is purchased:

$$
\begin{aligned}
\max_{g, x} & \quad \sum_{g \in G} x_g \\
\text{s.t.} & \quad \sum_{i \in I_g} g_i \ge \theta \cdot x_g & & \forall g \in G \\
& \quad \sum_{i \in I_g} g_i \le G_{\max} \cdot |I_g| \cdot x_g & & \forall g \in G \\
& \quad \sum_{i \in I} \frac{a_{i,n}}{100} g_i \ge R_n & & \forall n \in N \\
& \quad \sum_{i \in I} \frac{p_i}{100} g_i \le \min(B, \beta \cdot C^\star) \\
& \quad x_g \in \{0, 1\} & & \forall g \in G \\
& \quad 0 \le g_i \le G_{\max} & & \forall i \in I
\end{aligned}
$$

where $I_g \subseteq I$ are the ingredients in food group $g$, $\beta = 1.05$ caps the cost at 5% above the cheapest plan's cost $C^\star$ (this is the "near-optimal" guarantee — the user does not pay more than 5% extra for variety), and the upper-bound coupling $\sum g_i \le G_{\max} \cdot |I_g| \cdot x_g$ forces every gram of group $g$ to be 0 when $x_g = 0$.

CBC handles this MIP comfortably for $|G| \le 13$ food groups; runtime is sub-100 ms on the demo personas. If the cost-cap binds and no feasible integer solution exists, we re-solve once with the AKG floor relaxed to $0.95 \cdot R_n$ and emit `diverse_constraint_relaxed: true` with reason `akg_bound_violated`. The UI surfaces this as an honest amber badge — the system never lies that diversification "succeeded" when it didn't.

In practice on Bu Sari: cheapest gives 6 food groups across 7 ingredients; varied gives **11 food groups across 14 ingredients** at the same Rp 60k. The trade-off (variety for a tiny cost premium of Rp 2,064) is what the LP makes possible — and what a heuristic would have to guess at.

## Sensitivity analysis

GiziGo implements sensitivity by **full ILP re-solve** under perturbed prices, not via dual variables. The perturbation request looks like

```json
{ "perturbations": [{"ingredient_id": "tkpi_NR014", "delta_pct": 50}] }
```

Each perturbation $\delta_i$ multiplies the price: $p_i' = p_i (1 + \delta_i / 100)$. The cost LP is re-run and the *cost delta* is reported. Latency stays under 500 ms on the demo personas.

We chose re-solve over dual variables because (a) constraint shadows can change discretely once the basis flips, so duals are not safe extrapolators across large perturbations; (b) the LP is small and CBC solves Cheapest from scratch in ~30-100 ms; (c) the UI is honest about *the actual new optimal*, not a linear approximation.

## Infeasibility analyzer

When *Cheapest* returns infeasible at the user's budget, GiziGo runs a **bisection on the budget**:

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
