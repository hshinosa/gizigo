import type { OptimizeRequest } from "../lib/types";

export type PersonaId = "bu_sari" | "anggaran_ekstrem";

export const PERSONAS: Record<PersonaId, OptimizeRequest> = {
  bu_sari: {
    members: [
      { member_id: "m1", label: "Pak Budi", akg_category: "adult_male_19_49" },
      { member_id: "m2", label: "Bu Sari (menyusui)", akg_category: "lactating_mother_0_6m" },
      { member_id: "m3", label: "Aldo (5th)", akg_category: "child_4_6" },
      { member_id: "m4", label: "Bayi (toddler)", akg_category: "toddler_1_3" },
    ],
    daily_budget_idr: 60000,
    region: "dki_jakarta",
    restrictions: [],
    plan_types: ["cheapest", "balanced", "diverse"],
  },
  anggaran_ekstrem: {
    members: [
      { member_id: "m1", label: "Ayah", akg_category: "adult_male_19_49" },
      { member_id: "m2", label: "Ibu", akg_category: "adult_female_19_49" },
      { member_id: "m3", label: "Remaja Pria", akg_category: "teen_male_13_15" },
      { member_id: "m4", label: "Remaja Wanita", akg_category: "teen_female_13_15" },
      { member_id: "m5", label: "Anak SD", akg_category: "child_4_6" },
    ],
    daily_budget_idr: 25000,
    region: "national_baseline",
    restrictions: [],
    plan_types: ["cheapest", "balanced"],
  },
};
