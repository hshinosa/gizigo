import type { OptimizeRequest } from "../lib/types";

export type PersonaId = "bu_sari" | "anggaran_ekstrem" | "mbg_sppg";

export const PERSONAS: Record<PersonaId, OptimizeRequest> = {
  bu_sari: {
    members: [
      { member_id: "m1", label: "Father", akg_category: "adult_male_19_49" },
      { member_id: "m2", label: "Bu Sari (lactating)", akg_category: "lactating_mother_0_6m" },
      { member_id: "m3", label: "Aldo (5 yrs)", akg_category: "child_4_6" },
      { member_id: "m4", label: "Baby (toddler)", akg_category: "toddler_1_3" },
    ],
    daily_budget_idr: 60000,
    region: "dki_jakarta",
    restrictions: [],
    plan_types: ["cheapest", "balanced", "diverse"],
  },
  anggaran_ekstrem: {
    members: [
      { member_id: "m1", label: "Father", akg_category: "adult_male_19_49" },
      { member_id: "m2", label: "Mother", akg_category: "adult_female_19_49" },
      { member_id: "m3", label: "Teen Boy", akg_category: "teen_male_13_15" },
      { member_id: "m4", label: "Teen Girl", akg_category: "teen_female_13_15" },
      { member_id: "m5", label: "Schoolchild", akg_category: "child_4_6" },
    ],
    daily_budget_idr: 25000,
    region: "national_baseline",
    restrictions: [],
    plan_types: ["cheapest", "balanced"],
  },
  mbg_sppg: {
    members: [
      { member_id: "m1", label: "Primary student", akg_category: "child_4_6" },
    ],
    daily_budget_idr: 12000,
    region: "national_baseline",
    restrictions: [],
    plan_types: ["cheapest", "balanced", "diverse"],
  },
};
