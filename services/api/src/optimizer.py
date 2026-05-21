from __future__ import annotations

import hashlib
import json
import os
import time
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Literal, cast

import pulp

from .data import (
    AkgTable,
    Catalog,
    Ingredient,
    PriceTable,
    aggregate_household_akg,
)
from .models import (
    NUTRIENT_KEYS,
    AkgCategory,
    HouseholdMember,
    IngredientUse,
    InfeasibilityHint,
    NutrientAchievement,
    Plan,
    PlanType,
    Restriction,
    SolveStatus,
)

NUTRIENT_UNITS: dict[str, str] = {
    "energy_kcal": "kcal",
    "protein_g": "g",
    "fat_g": "g",
    "carbohydrate_g": "g",
    "iron_mg": "mg",
    "zinc_mg": "mg",
    "vitamin_a_ug_rae": "µg RAE",
    "calcium_mg": "mg",
}

PLAN_LABEL: dict[str, str] = {
    "cheapest": "Cheapest",
    "balanced": "Most Balanced",
    "diverse": "Most Varied",
}

MEAL_SLOT_BY_GROUP: dict[str, str] = {
    "serealia": "makan_siang",
    "umbi": "makan_malam",
    "kacang": "makan_siang",
    "sayur": "makan_siang",
    "buah": "kudapan",
    "daging": "makan_malam",
    "ikan": "makan_siang",
    "telur": "sarapan",
    "susu": "sarapan",
    "bumbu": "makan_siang",
    "minyak": "makan_siang",
    "konfeksioneri": "kudapan",
    "minuman": "kudapan",
}

MIN_GRAMS_THRESHOLD = 10.0
MAX_GRAMS_PER_INGREDIENT = 1500.0
BALANCED_SLACK_WEIGHT = 50.0


@dataclass(frozen=True)
class SolverInputs:
    catalog: Catalog
    prices: PriceTable
    akg: AkgTable
    members: tuple[HouseholdMember, ...]
    daily_budget_idr: int
    restrictions: tuple[Restriction, ...]


@dataclass(frozen=True)
class SolveResult:
    status: SolveStatus
    total_cost_idr: float
    grams_by_ingredient: dict[str, float]
    achieved: dict[str, float]
    elapsed_ms: int


def _solver() -> pulp.PULP_CBC_CMD:
    return pulp.PULP_CBC_CMD(
        msg=False,
        threads=1,
        presolve=True,
        cuts=False,
        options=["randomS 1"],
        timeLimit=10,
    )


def _eligible_ingredients(inputs: SolverInputs) -> list[Ingredient]:
    catalog_by_id = inputs.catalog.by_id()
    eligible: list[Ingredient] = []
    excluded_lower = {r.target.strip().lower() for r in inputs.restrictions}
    for iid, price in inputs.prices.prices_per_100g.items():
        if iid not in catalog_by_id:
            continue
        if price <= 0:
            continue
        ing = catalog_by_id[iid]
        if any(token in ing.display_name.lower() for token in excluded_lower):
            continue
        if any(token in ing.food_group.lower() for token in excluded_lower):
            continue
        eligible.append(ing)
    return eligible


def _household_requirements(inputs: SolverInputs) -> dict[str, float]:
    cats: list[AkgCategory] = [m.akg_category for m in inputs.members]
    return aggregate_household_akg(cats, inputs.akg)


def _add_common_constraints(
    prob: pulp.LpProblem,
    grams: dict[str, pulp.LpVariable],
    eligible: list[Ingredient],
    inputs: SolverInputs,
) -> None:
    cost_terms = []
    for ing in eligible:
        price_per_100 = inputs.prices.prices_per_100g[ing.ingredient_id]
        cost_terms.append((price_per_100 / 100.0) * grams[ing.ingredient_id])
    prob += pulp.lpSum(cost_terms) <= inputs.daily_budget_idr, "budget"


def _nutrient_term(grams: dict[str, pulp.LpVariable], eligible: list[Ingredient], nutrient: str) -> pulp.LpAffineExpression:
    return pulp.lpSum(
        (ing.nutrients_per_100g[nutrient] / 100.0) * grams[ing.ingredient_id] for ing in eligible
    )


def _cost_term(grams: dict[str, pulp.LpVariable], eligible: list[Ingredient], inputs: SolverInputs) -> pulp.LpAffineExpression:
    return pulp.lpSum(
        (inputs.prices.prices_per_100g[ing.ingredient_id] / 100.0) * grams[ing.ingredient_id] for ing in eligible
    )


def _make_grams_vars(eligible: Iterable[Ingredient]) -> dict[str, pulp.LpVariable]:
    return {
        ing.ingredient_id: pulp.LpVariable(
            name=f"g_{ing.ingredient_id}",
            lowBound=0.0,
            upBound=MAX_GRAMS_PER_INGREDIENT,
            cat=pulp.LpContinuous,
        )
        for ing in eligible
    }


def _evaluate(grams_values: dict[str, float], eligible: list[Ingredient]) -> dict[str, float]:
    achieved = {k: 0.0 for k in NUTRIENT_KEYS}
    for ing in eligible:
        g = grams_values.get(ing.ingredient_id, 0.0)
        if g <= 0:
            continue
        for k in NUTRIENT_KEYS:
            achieved[k] += (ing.nutrients_per_100g[k] / 100.0) * g
    return achieved


def solve_cheapest(inputs: SolverInputs) -> SolveResult:
    started = time.perf_counter()
    eligible = _eligible_ingredients(inputs)
    if not eligible:
        return SolveResult("infeasible", 0.0, {}, {k: 0.0 for k in NUTRIENT_KEYS}, 0)

    requirements = _household_requirements(inputs)
    grams = _make_grams_vars(eligible)

    prob = pulp.LpProblem("cheapest", pulp.LpMinimize)
    prob += _cost_term(grams, eligible, inputs)
    _add_common_constraints(prob, grams, eligible, inputs)

    for n in NUTRIENT_KEYS:
        prob += _nutrient_term(grams, eligible, n) >= requirements[n], f"req_{n}"

    prob.solve(_solver())
    status = pulp.LpStatus[prob.status]
    elapsed_ms = int((time.perf_counter() - started) * 1000)

    if status != "Optimal":
        return SolveResult("infeasible", 0.0, {}, {k: 0.0 for k in NUTRIENT_KEYS}, elapsed_ms)

    grams_values = {ing.ingredient_id: grams[ing.ingredient_id].value() or 0.0 for ing in eligible}
    achieved = _evaluate(grams_values, eligible)
    total_cost = sum(
        (inputs.prices.prices_per_100g[iid] / 100.0) * v for iid, v in grams_values.items()
    )
    return SolveResult("optimal", float(total_cost), grams_values, achieved, elapsed_ms)


def solve_balanced(inputs: SolverInputs) -> SolveResult:
    started = time.perf_counter()
    eligible = _eligible_ingredients(inputs)
    if not eligible:
        return SolveResult("infeasible", 0.0, {}, {k: 0.0 for k in NUTRIENT_KEYS}, 0)

    requirements = _household_requirements(inputs)
    grams = _make_grams_vars(eligible)
    slack = {
        n: pulp.LpVariable(f"slack_{n}", lowBound=0.0, cat=pulp.LpContinuous)
        for n in NUTRIENT_KEYS
    }

    prob = pulp.LpProblem("balanced", pulp.LpMinimize)
    prob += _cost_term(grams, eligible, inputs) + BALANCED_SLACK_WEIGHT * pulp.lpSum(slack.values())
    _add_common_constraints(prob, grams, eligible, inputs)

    for n in NUTRIENT_KEYS:
        prob += (_nutrient_term(grams, eligible, n) + slack[n]) >= requirements[n], f"req_{n}"

    prob.solve(_solver())
    status = pulp.LpStatus[prob.status]
    elapsed_ms = int((time.perf_counter() - started) * 1000)

    if status != "Optimal":
        return SolveResult("infeasible", 0.0, {}, {k: 0.0 for k in NUTRIENT_KEYS}, elapsed_ms)

    grams_values = {ing.ingredient_id: grams[ing.ingredient_id].value() or 0.0 for ing in eligible}
    achieved = _evaluate(grams_values, eligible)
    total_cost = sum(
        (inputs.prices.prices_per_100g[iid] / 100.0) * v for iid, v in grams_values.items()
    )
    return SolveResult("optimal", float(total_cost), grams_values, achieved, elapsed_ms)


def derive_diverse(cheapest: SolveResult, inputs: SolverInputs) -> tuple[SolveResult, bool, str | None]:
    if cheapest.status != "optimal":
        return cheapest, True, "underlying_cheapest_infeasible"

    catalog = inputs.catalog.by_id()
    eligible_by_id = {ing.ingredient_id: ing for ing in _eligible_ingredients(inputs)}
    used = {iid: g for iid, g in cheapest.grams_by_ingredient.items() if g >= MIN_GRAMS_THRESHOLD}
    used_groups = {eligible_by_id[i].food_group for i in used if i in eligible_by_id}

    candidate_groups = sorted(
        {ing.food_group for ing in eligible_by_id.values()} - used_groups,
    )
    target_group_increase = 2

    if not candidate_groups:
        return cheapest, True, "no_unused_food_groups"

    requirements = _household_requirements(inputs)

    grams_values = dict(cheapest.grams_by_ingredient)
    swaps_done = 0
    relaxed = False
    reason: str | None = None

    for new_group in candidate_groups[:target_group_increase]:
        new_group_candidates = sorted(
            (ing for ing in eligible_by_id.values() if ing.food_group == new_group),
            key=lambda ing: inputs.prices.prices_per_100g[ing.ingredient_id],
        )
        if not new_group_candidates:
            continue

        donor_id = _pick_donor_ingredient(grams_values, eligible_by_id, used_groups, inputs)
        if donor_id is None:
            relaxed = True
            reason = "akg_bound_violated"
            break

        ing_new = new_group_candidates[0]
        donor_grams = grams_values.get(donor_id, 0.0)
        donor_price_per_g = inputs.prices.prices_per_100g[donor_id] / 100.0
        donor_cost = donor_grams * donor_price_per_g
        new_price_per_g = inputs.prices.prices_per_100g[ing_new.ingredient_id] / 100.0

        candidate_grams = donor_cost / new_price_per_g if new_price_per_g > 0 else 0.0
        candidate_grams = min(candidate_grams, MAX_GRAMS_PER_INGREDIENT)
        if candidate_grams < MIN_GRAMS_THRESHOLD:
            candidate_grams = max(MIN_GRAMS_THRESHOLD, candidate_grams)

        trial_values = dict(grams_values)
        trial_values[donor_id] = 0.0
        trial_values[ing_new.ingredient_id] = trial_values.get(ing_new.ingredient_id, 0.0) + candidate_grams
        trial_achieved = _evaluate(trial_values, list(eligible_by_id.values()))
        trial_cost = sum(
            (inputs.prices.prices_per_100g[iid] / 100.0) * v for iid, v in trial_values.items()
        )

        if trial_cost > inputs.daily_budget_idr:
            relaxed = True
            reason = "budget_exhausted"
            break
        if any(trial_achieved[k] < requirements[k] * 0.95 for k in NUTRIENT_KEYS):
            relaxed = True
            reason = "akg_bound_violated"
            break

        grams_values = trial_values
        used_groups.add(new_group)
        swaps_done += 1

    final_achieved = _evaluate(grams_values, list(eligible_by_id.values()))
    final_cost = sum(
        (inputs.prices.prices_per_100g[iid] / 100.0) * v for iid, v in grams_values.items()
    )
    new_status: SolveStatus = "infeasible_relaxed" if relaxed else "optimal"
    return (
        SolveResult(new_status, float(final_cost), grams_values, final_achieved, cheapest.elapsed_ms),
        relaxed,
        reason if relaxed else None,
    )


def _pick_donor_ingredient(
    grams_values: dict[str, float],
    eligible_by_id: dict[str, Ingredient],
    used_groups: set[str],
    inputs: SolverInputs,
) -> str | None:
    best_id = None
    best_density = float("inf")
    for iid, g in grams_values.items():
        if g < MIN_GRAMS_THRESHOLD or iid not in eligible_by_id:
            continue
        ing = eligible_by_id[iid]
        if ing.food_group not in used_groups:
            continue
        score = sum(ing.nutrients_per_100g[n] for n in ("protein_g", "iron_mg", "zinc_mg", "calcium_mg", "vitamin_a_ug_rae"))
        rupiah_per_g = inputs.prices.prices_per_100g[iid] / 100.0
        if rupiah_per_g <= 0:
            continue
        density = score / rupiah_per_g if score > 0 else 0
        if density < best_density and density >= 0:
            best_density = density
            best_id = iid
    return best_id


def analyze_infeasibility(inputs: SolverInputs) -> InfeasibilityHint | None:
    eligible = _eligible_ingredients(inputs)
    if not eligible:
        return InfeasibilityHint(
            error_code="INFEASIBLE_RESTRICTIONS",
            message="Tidak ada bahan pangan yang lolos pembatasan. Coba longgarkan pembatasan.",
        )

    high_budget_inputs = SolverInputs(
        catalog=inputs.catalog,
        prices=inputs.prices,
        akg=inputs.akg,
        members=inputs.members,
        daily_budget_idr=inputs.daily_budget_idr * 100,
        restrictions=inputs.restrictions,
    )
    high = solve_cheapest(high_budget_inputs)
    if high.status != "optimal":
        requirements = _household_requirements(inputs)
        deficits = [n for n in NUTRIENT_KEYS if high.achieved[n] < requirements[n] * 0.99]
        return InfeasibilityHint(
            error_code="INFEASIBLE_RESTRICTIONS",
            message="Restrictions are too strict — no ingredient combination meets the RDA.",
            deficit_nutrients=deficits,
        )

    lo, hi = 0, inputs.daily_budget_idr * 100
    feasible_at_hi = True
    if not feasible_at_hi:
        return None
    for _ in range(20):
        if hi - lo <= max(1000, inputs.daily_budget_idr // 100):
            break
        mid = (lo + hi) // 2
        trial_inputs = SolverInputs(
            catalog=inputs.catalog,
            prices=inputs.prices,
            akg=inputs.akg,
            members=inputs.members,
            daily_budget_idr=mid,
            restrictions=inputs.restrictions,
        )
        result = solve_cheapest(trial_inputs)
        if result.status == "optimal":
            hi = mid
        else:
            lo = mid

    minimum = ((hi // 1000) + 1) * 1000
    requirements = _household_requirements(inputs)
    deficits = [n for n in NUTRIENT_KEYS if high.achieved[n] < requirements[n]]
    return InfeasibilityHint(
        error_code="INFEASIBLE_BUDGET_TOO_LOW",
        message=f"Budget too low. Estimated minimum Rp {minimum:,}.".replace(",", "."),
        minimum_feasible_budget_idr=minimum,
        deficit_nutrients=deficits,
    )


def to_plan(
    plan_type: str,
    result: SolveResult,
    inputs: SolverInputs,
    relaxed: bool = False,
    relaxation_reason: str | None = None,
) -> Plan:
    catalog_by_id = inputs.catalog.by_id()
    requirements = _household_requirements(inputs)

    ingredients_used: list[IngredientUse] = []
    food_groups: set[str] = set()
    for iid, g in sorted(result.grams_by_ingredient.items()):
        if g < MIN_GRAMS_THRESHOLD:
            continue
        ing = catalog_by_id.get(iid)
        if ing is None:
            continue
        food_groups.add(ing.food_group)
        slot = MEAL_SLOT_BY_GROUP.get(ing.food_group, "makan_siang")
        cost = (inputs.prices.prices_per_100g[iid] / 100.0) * g
        ingredients_used.append(IngredientUse(
            ingredient_id=iid,
            display_name=ing.display_name,
            food_group=ing.food_group,
            grams=round(g, 1),
            cost_idr=round(cost, 0),
            meal_slot=cast("Literal['sarapan', 'makan_siang', 'makan_malam', 'kudapan']", slot),
        ))

    achievement = []
    for n in NUTRIENT_KEYS:
        req = requirements[n]
        ach = result.achieved.get(n, 0.0)
        pct = (ach / req * 100.0) if req > 0 else 0.0
        achievement.append(NutrientAchievement(
            nutrient=n,
            achieved=round(ach, 2),
            required=round(req, 2),
            pct=round(pct, 1),
            unit=NUTRIENT_UNITS[n],
        ))

    return Plan(
        plan_type=cast("PlanType", plan_type),
        plan_label=PLAN_LABEL[plan_type],
        status=result.status,
        total_cost_idr=round(result.total_cost_idr, 0),
        ingredients=ingredients_used,
        achievement=achievement,
        diverse_constraint_relaxed=relaxed,
        relaxation_reason=relaxation_reason,
        food_group_count=len(food_groups),
    )


def compute_plan_hash(payload: dict[str, object]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:24]


def configure_determinism() -> None:
    os.environ.setdefault("PYTHONHASHSEED", "0")
