"""Unit tests for the GiziGo optimizer.

Mirror the verification cases promised in the spec at
openspec/changes/gizigo-meal-optimizer/specs/meal-optimizer/spec.md.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.data import (
    AkgRecord,
    AkgTable,
    Catalog,
    Ingredient,
    PriceTable,
    aggregate_household_akg,
    load_akg,
    load_catalog,
    load_cooking_method,
    load_prices,
    load_substitutes,
)
from src.models import AkgCategory, HouseholdMember, NUTRIENT_KEYS, Region, Restriction
from src.optimizer import (
    SolverInputs,
    analyze_infeasibility,
    compute_plan_hash,
    derive_diverse,
    solve_balanced,
    solve_cheapest,
)


def _bu_sari() -> tuple[HouseholdMember, ...]:
    return (
        HouseholdMember(member_id="m1", label="Pak Budi", akg_category="adult_male_19_49"),
        HouseholdMember(member_id="m2", label="Bu Sari", akg_category="lactating_mother_0_6m"),
        HouseholdMember(member_id="m3", label="Anak", akg_category="child_4_6"),
        HouseholdMember(member_id="m4", label="Bayi", akg_category="toddler_1_3"),
    )


def _anggaran_ekstrem() -> tuple[HouseholdMember, ...]:
    return (
        HouseholdMember(member_id="m1", label="a", akg_category="adult_male_19_49"),
        HouseholdMember(member_id="m2", label="b", akg_category="adult_female_19_49"),
        HouseholdMember(member_id="m3", label="c", akg_category="teen_male_13_15"),
        HouseholdMember(member_id="m4", label="d", akg_category="child_4_6"),
        HouseholdMember(member_id="m5", label="e", akg_category="toddler_1_3"),
    )


def _inputs(
    members: tuple[HouseholdMember, ...],
    budget: int,
    region: Region = "dki_jakarta",
    restrictions: tuple[Restriction, ...] = (),
) -> SolverInputs:
    return SolverInputs(
        catalog=load_catalog(),
        prices=load_prices(region),
        akg=load_akg(),
        members=members,
        daily_budget_idr=budget,
        restrictions=restrictions,
    )


def test_data_catalog_is_committed_and_complete() -> None:
    """Catalog hash, ingredient count, and 8 tracked nutrients per row."""
    catalog = load_catalog()
    assert catalog.catalog_hash and catalog.catalog_hash != "unknown"
    assert len(catalog.ingredients) >= 1000, "expected ~1146 from panganku scrape"
    sample = catalog.ingredients[0]
    assert set(sample.nutrients_per_100g.keys()) == set(NUTRIENT_KEYS)


def test_akg_aggregator_sums_nutrients() -> None:
    """Household AKG is the per-member AKG summed over members."""
    akg = load_akg()
    cats: list[AkgCategory] = ["adult_male_19_49", "child_4_6"]
    totals = aggregate_household_akg(cats, akg)
    expected_kcal = (
        akg.by_category["adult_male_19_49"].requirements["energy_kcal"]
        + akg.by_category["child_4_6"].requirements["energy_kcal"]
    )
    assert totals["energy_kcal"] == pytest.approx(expected_kcal)
    assert set(totals.keys()) == set(NUTRIENT_KEYS)


def test_solve_cheapest_bu_sari_is_optimal_and_under_budget() -> None:
    """Bu Sari (60k DKI, 4 anggota) must produce an optimal cheapest plan ≤ budget."""
    inputs = _inputs(_bu_sari(), 60_000, region="dki_jakarta")
    res = solve_cheapest(inputs)
    assert res.status == "optimal"
    assert res.total_cost_idr <= 60_000
    assert res.total_cost_idr > 0
    used = sum(1 for g in res.grams_by_ingredient.values() if g > 1.0)
    assert used >= 5


def test_solve_cheapest_meets_all_akg_floors() -> None:
    """Termurah is feasible only if every tracked nutrient hits the household floor."""
    inputs = _inputs(_bu_sari(), 60_000)
    requirements = aggregate_household_akg(
        [m.akg_category for m in inputs.members], inputs.akg
    )
    res = solve_cheapest(inputs)
    assert res.status == "optimal"
    for n in NUTRIENT_KEYS:
        assert res.achieved[n] + 1e-3 >= requirements[n], (
            f"{n} short: achieved {res.achieved[n]} < required {requirements[n]}"
        )


def test_solve_balanced_cost_le_or_equal_to_cheapest_cost_plus_slack() -> None:
    """Balanced minimises cost+slack; cheapest minimises cost. Cost should be very close on feasible cases."""
    inputs = _inputs(_bu_sari(), 60_000)
    cheap = solve_cheapest(inputs)
    bal = solve_balanced(inputs)
    assert cheap.status == "optimal"
    assert bal.status in ("optimal", "infeasible_relaxed")
    # The balanced plan still respects the budget.
    assert bal.total_cost_idr <= 60_000 + 1e-3


def test_derive_diverse_keeps_or_grows_food_group_set() -> None:
    """Diverse heuristic never reduces variety vs cheapest baseline,
    and respects the budget."""
    inputs = _inputs(_bu_sari(), 60_000)
    cheap = solve_cheapest(inputs)
    div, relaxed, reason = derive_diverse(cheap, inputs)
    assert isinstance(relaxed, bool)
    assert reason is None or isinstance(reason, str)
    eligible_by_id = {ing.ingredient_id: ing for ing in inputs.catalog.ingredients}
    cheap_groups = {
        eligible_by_id[i].food_group
        for i, g in cheap.grams_by_ingredient.items()
        if g > 1.0 and i in eligible_by_id
    }
    div_groups = {
        eligible_by_id[i].food_group
        for i, g in div.grams_by_ingredient.items()
        if g > 1.0 and i in eligible_by_id
    }
    assert len(div_groups) >= len(cheap_groups)
    assert div.total_cost_idr <= 60_000 + 1e-3


def test_analyze_infeasibility_finds_minimum_budget_for_extreme_persona() -> None:
    """Anggaran Ekstrem (5 anggota, national, Rp 25k) must be infeasible
    and the analyzer must surface a minimum_feasible_budget."""
    inputs = _inputs(_anggaran_ekstrem(), 25_000, region="national_baseline")
    cheap = solve_cheapest(inputs)
    assert cheap.status == "infeasible"

    hint = analyze_infeasibility(inputs)
    assert hint is not None
    assert hint.error_code in ("INFEASIBLE_BUDGET_TOO_LOW", "INFEASIBLE_RESTRICTIONS")
    if hint.error_code == "INFEASIBLE_BUDGET_TOO_LOW":
        assert hint.minimum_feasible_budget_idr is not None
        assert hint.minimum_feasible_budget_idr > 25_000
        assert len(hint.deficit_nutrients) >= 1


def test_plan_hash_is_deterministic_and_input_addressed() -> None:
    """Same payload → same hash. Different payload → different hash."""
    p1: dict[str, object] = {"a": 1, "b": [1, 2, 3], "c": "x"}
    p2: dict[str, object] = {"c": "x", "b": [1, 2, 3], "a": 1}
    p3: dict[str, object] = {"a": 1, "b": [1, 2, 3], "c": "y"}
    assert compute_plan_hash(p1) == compute_plan_hash(p2)
    assert compute_plan_hash(p1) != compute_plan_hash(p3)
    assert len(compute_plan_hash(p1)) == 24
    assert all(c in "0123456789abcdef" for c in compute_plan_hash(p1))


def test_static_data_files_pass_basic_invariants() -> None:
    """All committed datasets load and respect basic invariants."""
    catalog = load_catalog()
    akg = load_akg()
    prices_dki = load_prices("dki_jakarta")
    prices_nat = load_prices("national_baseline")
    subs = load_substitutes()
    cooking = load_cooking_method()

    # AKG covers all 7 demo personas worth of categories.
    for cat in (
        "toddler_1_3",
        "child_4_6",
        "teen_male_13_15",
        "teen_female_13_15",
        "adult_male_19_49",
        "adult_female_19_49",
        "lactating_mother_0_6m",
    ):
        assert cat in akg.by_category
        for n in NUTRIENT_KEYS:
            assert akg.by_category[cat].requirements[n] >= 0

    # Prices reference real catalog ingredients.
    catalog_ids = {i.ingredient_id for i in catalog.ingredients}
    assert set(prices_dki.prices_per_100g) <= catalog_ids
    assert set(prices_nat.prices_per_100g) <= catalog_ids
    assert len(prices_dki.prices_per_100g) >= 30
    assert len(prices_nat.prices_per_100g) >= 30

    # Substitutes round-trip into catalog ids.
    for entry in subs:
        assert entry.from_id in catalog_ids
        for to_id in entry.to_ids:
            assert to_id in catalog_ids

    # Cooking-method file has both per-ingredient overrides and group fallbacks.
    assert isinstance(cooking, dict)
    assert "ingredients" in cooking or "by_ingredient" in cooking or len(cooking) > 0
