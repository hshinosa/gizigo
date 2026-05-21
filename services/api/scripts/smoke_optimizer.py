from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src import optimizer  # noqa: E402
from src.data import load_akg, load_catalog, load_prices  # noqa: E402
from src.models import HouseholdMember, OptimizeRequest  # noqa: E402


def main() -> int:
    optimizer.configure_determinism()
    catalog = load_catalog()
    akg = load_akg()
    prices = load_prices("dki_jakarta")
    print(f"catalog: {len(catalog.ingredients)} ingredients (hash {catalog.catalog_hash})")
    print(f"prices DKI: {len(prices.prices_per_100g)} priced ingredients")
    print(f"AKG categories: {list(akg.by_category.keys())}")

    req = OptimizeRequest(
        members=[
            HouseholdMember(member_id="m1", label="Ayah", akg_category="adult_male_19_49"),
            HouseholdMember(member_id="m2", label="Ibu (menyusui)", akg_category="lactating_mother_0_6m"),
            HouseholdMember(member_id="m3", label="Anak 1", akg_category="child_4_6"),
            HouseholdMember(member_id="m4", label="Balita", akg_category="toddler_1_3"),
        ],
        daily_budget_idr=60000,
        region="dki_jakarta",
        restrictions=[],
        plan_types=["cheapest", "balanced", "diverse"],
    )

    inputs = optimizer.SolverInputs(
        catalog=catalog,
        prices=prices,
        akg=akg,
        members=tuple(req.members),
        daily_budget_idr=req.daily_budget_idr,
        restrictions=tuple(req.restrictions),
    )

    print("\n--- Termurah ---")
    cheap = optimizer.solve_cheapest(inputs)
    print(f"status={cheap.status} cost=Rp {cheap.total_cost_idr:,.0f} elapsed={cheap.elapsed_ms}ms")
    if cheap.status == "optimal":
        plan = optimizer.to_plan("cheapest", cheap, inputs)
        print(f"food_groups={plan.food_group_count}")
        for u in plan.ingredients:
            print(f"  {u.grams:6.1f}g  {u.display_name[:50]:50s}  Rp {u.cost_idr:6,.0f}  ({u.food_group}/{u.meal_slot})")
        for a in plan.achievement:
            print(f"  AKG {a.nutrient:18s} {a.achieved:8.1f}/{a.required:8.1f} {a.unit:8s} = {a.pct:6.1f}%")

    print("\n--- Paling Seimbang ---")
    bal = optimizer.solve_balanced(inputs)
    print(f"status={bal.status} cost=Rp {bal.total_cost_idr:,.0f} elapsed={bal.elapsed_ms}ms")
    if bal.status == "optimal":
        plan = optimizer.to_plan("balanced", bal, inputs)
        print(f"food_groups={plan.food_group_count}")

    print("\n--- Paling Beragam ---")
    if cheap.status == "optimal":
        diverse, relaxed, reason = optimizer.derive_diverse(cheap, inputs)
        plan = optimizer.to_plan("diverse", diverse, inputs, relaxed=relaxed, relaxation_reason=reason)
        print(f"status={diverse.status} cost=Rp {diverse.total_cost_idr:,.0f} relaxed={relaxed} reason={reason}")
        print(f"food_groups={plan.food_group_count}")

    print("\n--- Anggaran Ekstrem (infeasibility) ---")
    extreme_inputs = optimizer.SolverInputs(
        catalog=catalog,
        prices=load_prices("national_baseline"),
        akg=akg,
        members=tuple([
            HouseholdMember(member_id="m1", label="Ayah", akg_category="adult_male_19_49"),
            HouseholdMember(member_id="m2", label="Ibu", akg_category="adult_female_19_49"),
            HouseholdMember(member_id="m3", label="Remaja Pria", akg_category="teen_male_13_15"),
            HouseholdMember(member_id="m4", label="Remaja Wanita", akg_category="teen_female_13_15"),
            HouseholdMember(member_id="m5", label="Anak", akg_category="child_4_6"),
        ]),
        daily_budget_idr=25000,
        restrictions=tuple(),
    )
    ext = optimizer.solve_cheapest(extreme_inputs)
    print(f"status={ext.status}")
    if ext.status != "optimal":
        hint = optimizer.analyze_infeasibility(extreme_inputs)
        print(f"infeasibility hint: {hint.model_dump() if hint else None}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
