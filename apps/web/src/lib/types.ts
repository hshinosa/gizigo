import { z } from "zod";

export const AkgCategoryZ = z.enum([
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
]);
export type AkgCategory = z.infer<typeof AkgCategoryZ>;

export const RegionZ = z.enum([
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
]);
export type Region = z.infer<typeof RegionZ>;

export const PlanTypeZ = z.enum(["cheapest", "balanced", "diverse"]);
export type PlanType = z.infer<typeof PlanTypeZ>;

export const RestrictionTypeZ = z.enum(["allergy", "religious", "dislike"]);
export type RestrictionType = z.infer<typeof RestrictionTypeZ>;

export const MealSlotZ = z.enum(["sarapan", "makan_siang", "makan_malam", "kudapan"]);
export type MealSlot = z.infer<typeof MealSlotZ>;

export const HouseholdMemberZ = z.object({
  member_id: z.string(),
  label: z.string(),
  akg_category: AkgCategoryZ,
});
export type HouseholdMember = z.infer<typeof HouseholdMemberZ>;

export const RestrictionZ = z.object({
  type: RestrictionTypeZ,
  target: z.string(),
});
export type Restriction = z.infer<typeof RestrictionZ>;

export const OptimizeRequestZ = z.object({
  members: z.array(HouseholdMemberZ).min(1),
  daily_budget_idr: z.number().int().min(0).max(2_000_000),
  region: RegionZ,
  restrictions: z.array(RestrictionZ),
  plan_types: z.array(PlanTypeZ).min(1),
});
export type OptimizeRequest = z.infer<typeof OptimizeRequestZ>;

export const IngredientUseZ = z.object({
  ingredient_id: z.string(),
  display_name: z.string(),
  food_group: z.string(),
  grams: z.number(),
  cost_idr: z.number(),
  meal_slot: MealSlotZ,
});
export type IngredientUse = z.infer<typeof IngredientUseZ>;

export const NutrientAchievementZ = z.object({
  nutrient: z.string(),
  achieved: z.number(),
  required: z.number(),
  pct: z.number(),
  unit: z.string(),
});
export type NutrientAchievement = z.infer<typeof NutrientAchievementZ>;

export const SolveStatusZ = z.enum(["optimal", "infeasible", "infeasible_relaxed"]);
export type SolveStatus = z.infer<typeof SolveStatusZ>;

export const PlanZ = z.object({
  plan_type: PlanTypeZ,
  plan_label: z.string(),
  status: SolveStatusZ,
  total_cost_idr: z.number(),
  ingredients: z.array(IngredientUseZ),
  achievement: z.array(NutrientAchievementZ),
  diverse_constraint_relaxed: z.boolean(),
  relaxation_reason: z.string().nullable().optional(),
  food_group_count: z.number(),
});
export type Plan = z.infer<typeof PlanZ>;

export const InfeasibilityHintZ = z.object({
  error_code: z.enum(["INFEASIBLE_BUDGET_TOO_LOW", "INFEASIBLE_RESTRICTIONS"]),
  message: z.string(),
  minimum_feasible_budget_idr: z.number().nullable().optional(),
  deficit_nutrients: z.array(z.string()),
});
export type InfeasibilityHint = z.infer<typeof InfeasibilityHintZ>;

export const OptimizeResponseZ = z.object({
  request_id: z.string(),
  plan_hash: z.string(),
  plans: z.array(PlanZ),
  infeasibility: InfeasibilityHintZ.nullable().optional(),
  catalog_hash: z.string(),
  elapsed_ms: z.number(),
});
export type OptimizeResponse = z.infer<typeof OptimizeResponseZ>;

export const SensitivityResponseZ = z.object({
  request_id: z.string(),
  base_plan_hash: z.string(),
  perturbed_plan_hash: z.string(),
  plans: z.array(PlanZ),
  cost_delta_idr: z.number(),
  elapsed_ms: z.number(),
});
export type SensitivityResponse = z.infer<typeof SensitivityResponseZ>;

export const ApiErrorZ = z.object({
  error_code: z.string(),
  message: z.string(),
  request_id: z.string(),
  details: z.unknown().optional().nullable(),
});
export type ApiError = z.infer<typeof ApiErrorZ>;
