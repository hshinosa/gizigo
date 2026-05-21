from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

NUTRIENT_KEYS: tuple[str, ...] = (
    "energy_kcal",
    "protein_g",
    "fat_g",
    "carbohydrate_g",
    "fiber_g",
    "iron_mg",
    "zinc_mg",
    "vitamin_a_ug_rae",
    "calcium_mg",
)

PlanType = Literal["cheapest", "balanced", "diverse"]
RestrictionType = Literal["allergy", "religious", "dislike"]
AkgCategory = Literal[
    "infant_7_11m",
    "toddler_1_3",
    "child_4_6",
    "child_7_9",
    "teen_male_13_15",
    "teen_female_13_15",
    "teen_male_16_18",
    "teen_female_16_18",
    "adult_male_19_49",
    "adult_female_19_49",
    "elderly_male_65_plus",
    "elderly_female_65_plus",
    "lactating_mother_0_6m",
    "pregnant_trimester_2_3",
]
Region = Literal[
    "dki_jakarta",
    "national_baseline",
    "yogyakarta",
    "jawa_barat",
    "banten",
    "jawa_tengah",
    "jawa_timur",
    "aceh",
    "sumatera_utara",
    "sulawesi_selatan",
    "sulawesi_barat",
    "kalimantan_barat",
    "nusa_tenggara_barat",
    "nusa_tenggara_timur",
    "maluku",
    "papua",
]
SolveStatus = Literal["optimal", "infeasible", "infeasible_relaxed"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class HouseholdMember(StrictModel):
    member_id: str = Field(min_length=1, max_length=64)
    label: str = Field(min_length=1, max_length=80)
    akg_category: AkgCategory


class Restriction(StrictModel):
    type: RestrictionType
    target: str = Field(min_length=1, max_length=80)


class OptimizeRequest(StrictModel):
    members: list[HouseholdMember] = Field(min_length=1, max_length=10)
    daily_budget_idr: Annotated[int, Field(ge=0, le=2_000_000)]
    region: Region = "dki_jakarta"
    restrictions: list[Restriction] = Field(default_factory=list, max_length=20)
    plan_types: list[PlanType] = Field(default_factory=lambda: ["cheapest", "balanced"])

    @field_validator("plan_types")
    @classmethod
    def validate_plans(cls, v: list[PlanType]) -> list[PlanType]:
        if not v:
            raise ValueError("plan_types must contain at least one plan")
        if len(set(v)) != len(v):
            raise ValueError("plan_types must be unique")
        return v


class IngredientUse(StrictModel):
    ingredient_id: str
    display_name: str
    food_group: str
    grams: float = Field(ge=0)
    cost_idr: float = Field(ge=0)
    meal_slot: Literal["sarapan", "makan_siang", "makan_malam", "kudapan"]


class NutrientAchievement(StrictModel):
    nutrient: str
    achieved: float
    required: float
    pct: float
    unit: str


class Plan(StrictModel):
    plan_type: PlanType
    plan_label: str
    status: SolveStatus
    total_cost_idr: float
    ingredients: list[IngredientUse]
    achievement: list[NutrientAchievement]
    diverse_constraint_relaxed: bool = False
    relaxation_reason: str | None = None
    food_group_count: int


class InfeasibilityHint(StrictModel):
    error_code: Literal["INFEASIBLE_BUDGET_TOO_LOW", "INFEASIBLE_RESTRICTIONS"]
    message: str
    minimum_feasible_budget_idr: int | None = None
    deficit_nutrients: list[str] = Field(default_factory=list)


class OptimizeResponse(StrictModel):
    request_id: str
    plan_hash: str
    plans: list[Plan]
    infeasibility: InfeasibilityHint | None = None
    catalog_hash: str
    elapsed_ms: int


class SensitivityRequest(StrictModel):
    base_request: OptimizeRequest
    perturbations: list["IngredientPerturbation"] = Field(min_length=1, max_length=20)


class IngredientPerturbation(StrictModel):
    ingredient_id: str
    delta_pct: float = Field(ge=-90, le=300)


class SensitivityResponse(StrictModel):
    request_id: str
    base_plan_hash: str
    perturbed_plan_hash: str
    plans: list[Plan]
    cost_delta_idr: float
    elapsed_ms: int


class HumanizeRequest(StrictModel):
    plan: Plan
    use_llm: bool = False


class MealNarration(StrictModel):
    meal_slot: Literal["sarapan", "makan_siang", "makan_malam", "kudapan"]
    title: str
    description: str
    rendered_via: Literal["templated", "llm_validated", "llm_rejected_fallback_templated"]


class HumanizeResponse(StrictModel):
    request_id: str
    plan_hash: str
    meals: list[MealNarration]


class ApiError(StrictModel):
    error_code: str
    message: str
    request_id: str
    details: dict[str, object] | None = None


SensitivityRequest.model_rebuild()
