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
    "fiber_g": "g",
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
BALANCED_OVERSHOOT_WEIGHT = 2.0
BALANCED_OVERSHOOT_THRESHOLD = 1.3
DIVERSE_GROUP_PRESENCE_GRAMS = 50.0
DIVERSE_AKG_FLOOR_RELAXATION = 0.95
DIVERSE_BUDGET_HEADROOM = 1.05


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
    overshoot = {
        n: pulp.LpVariable(f"overshoot_{n}", lowBound=0.0, cat=pulp.LpContinuous)
        for n in NUTRIENT_KEYS
    }
    max_overshoot_ratio = pulp.LpVariable(
        "max_overshoot_ratio", lowBound=0.0, cat=pulp.LpContinuous,
    )

    prob = pulp.LpProblem("balanced", pulp.LpMinimize)
    prob += _cost_term(grams, eligible, inputs) + BALANCED_OVERSHOOT_WEIGHT * inputs.daily_budget_idr * max_overshoot_ratio
    _add_common_constraints(prob, grams, eligible, inputs)

    for n in NUTRIENT_KEYS:
        nutrient_expr = _nutrient_term(grams, eligible, n)
        prob += nutrient_expr >= requirements[n], f"req_{n}"
        prob += (
            nutrient_expr - overshoot[n] <= BALANCED_OVERSHOOT_THRESHOLD * requirements[n]
        ), f"cap_{n}"
        if requirements[n] > 0:
            prob += (
                overshoot[n] <= max_overshoot_ratio * requirements[n]
            ), f"max_overshoot_{n}"

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


def solve_diverse(
    inputs: SolverInputs,
    cheapest_cost: float | None = None,
) -> tuple[SolveResult, bool, str | None]:
    started = time.perf_counter()
    eligible = _eligible_ingredients(inputs)
    if not eligible:
        return (
            SolveResult("infeasible", 0.0, {}, {k: 0.0 for k in NUTRIENT_KEYS}, 0),
            True,
            "no_eligible_ingredients",
        )

    requirements = _household_requirements(inputs)
    grams = _make_grams_vars(eligible)

    food_groups = sorted({ing.food_group for ing in eligible})
    group_present = {
        g: pulp.LpVariable(f"present_{g}", cat=pulp.LpBinary)
        for g in food_groups
    }

    prob = pulp.LpProblem("diverse", pulp.LpMaximize)
    prob += pulp.lpSum(group_present.values())

    cost_expr = _cost_term(grams, eligible, inputs)
    prob += cost_expr <= inputs.daily_budget_idr, "budget"
    if cheapest_cost is not None and cheapest_cost > 0:
        prob += cost_expr <= DIVERSE_BUDGET_HEADROOM * cheapest_cost, "near_optimal_cost"

    for n in NUTRIENT_KEYS:
        prob += _nutrient_term(grams, eligible, n) >= requirements[n], f"req_{n}"

    for g in food_groups:
        ings_in_group = [ing for ing in eligible if ing.food_group == g]
        if not ings_in_group:
            continue
        group_grams = pulp.lpSum(grams[ing.ingredient_id] for ing in ings_in_group)
        prob += group_grams >= DIVERSE_GROUP_PRESENCE_GRAMS * group_present[g], f"present_min_{g}"
        max_group_grams = MAX_GRAMS_PER_INGREDIENT * len(ings_in_group)
        prob += group_grams <= max_group_grams * group_present[g], f"present_max_{g}"

    prob.solve(_solver())
    status = pulp.LpStatus[prob.status]
    elapsed_ms = int((time.perf_counter() - started) * 1000)

    relaxed = False
    reason: str | None = None

    if status != "Optimal":
        relaxed_inputs = SolverInputs(
            catalog=inputs.catalog,
            prices=inputs.prices,
            akg=inputs.akg,
            members=inputs.members,
            daily_budget_idr=inputs.daily_budget_idr,
            restrictions=inputs.restrictions,
        )
        relaxed_grams = _make_grams_vars(eligible)
        relaxed_groups = {
            g: pulp.LpVariable(f"r_present_{g}", cat=pulp.LpBinary)
            for g in food_groups
        }
        relaxed_prob = pulp.LpProblem("diverse_relaxed", pulp.LpMaximize)
        relaxed_prob += pulp.lpSum(relaxed_groups.values())
        relaxed_cost = _cost_term(relaxed_grams, eligible, relaxed_inputs)
        relaxed_prob += relaxed_cost <= inputs.daily_budget_idr, "budget"
        for n in NUTRIENT_KEYS:
            relaxed_prob += (
                _nutrient_term(relaxed_grams, eligible, n)
                >= DIVERSE_AKG_FLOOR_RELAXATION * requirements[n]
            ), f"req_{n}"
        for g in food_groups:
            ings_in_group = [ing for ing in eligible if ing.food_group == g]
            if not ings_in_group:
                continue
            group_grams = pulp.lpSum(relaxed_grams[ing.ingredient_id] for ing in ings_in_group)
            relaxed_prob += group_grams >= DIVERSE_GROUP_PRESENCE_GRAMS * relaxed_groups[g], f"present_min_{g}"
            max_group_grams = MAX_GRAMS_PER_INGREDIENT * len(ings_in_group)
            relaxed_prob += group_grams <= max_group_grams * relaxed_groups[g], f"present_max_{g}"
        relaxed_prob.solve(_solver())
        if pulp.LpStatus[relaxed_prob.status] != "Optimal":
            return (
                SolveResult("infeasible", 0.0, {}, {k: 0.0 for k in NUTRIENT_KEYS}, elapsed_ms),
                True,
                "akg_bound_violated",
            )
        grams = relaxed_grams
        relaxed = True
        reason = "akg_bound_violated"

    grams_values = {ing.ingredient_id: grams[ing.ingredient_id].value() or 0.0 for ing in eligible}
    achieved = _evaluate(grams_values, eligible)
    total_cost = sum(
        (inputs.prices.prices_per_100g[iid] / 100.0) * v for iid, v in grams_values.items()
    )

    if cheapest_cost is not None and cheapest_cost > 0 and total_cost > cheapest_cost * DIVERSE_BUDGET_HEADROOM + 1e-3:
        relaxed = True
        reason = "budget_exhausted"

    elapsed_ms = int((time.perf_counter() - started) * 1000)
    return (
        SolveResult("optimal", float(total_cost), grams_values, achieved, elapsed_ms),
        relaxed,
        reason,
    )


def derive_diverse(cheapest: SolveResult, inputs: SolverInputs) -> tuple[SolveResult, bool, str | None]:
    if cheapest.status != "optimal":
        return cheapest, True, "underlying_cheapest_infeasible"
    return solve_diverse(inputs, cheapest_cost=cheapest.total_cost_idr)


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
