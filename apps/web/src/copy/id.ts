export const COPY = {
  app: {
    title: "GiziGo",
    tagline: "Affordable daily meal plans that meet your family's nutritional needs.",
    subtitle: "Built on the Indonesian Food Composition Table (Kemenkes 2020) and Permenkes 28/2019 RDA values.",
  },
  household: {
    sectionTitle: "Family Members",
    addMember: "Add member",
    memberLabel: "Nickname",
    memberCategory: "RDA category",
    removeMember: "Remove",
    minOneMember: "At least 1 family member is required.",
  },
  budget: {
    sectionTitle: "Daily Budget",
    label: "Budget (Rp / day)",
    helper: "Drag the slider or type a number directly.",
  },
  region: {
    sectionTitle: "Price Region",
    options: {
      dki_jakarta: "DKI Jakarta",
      national_baseline: "National Median",
    },
  },
  restrictions: {
    sectionTitle: "Restrictions",
    placeholder: "Ingredient or group to avoid (e.g. fish, peanuts)",
    addLabel: "Add restriction",
    typeAllergy: "Allergy",
    typeReligious: "Religious",
    typeDislike: "Dislike",
  },
  persona: {
    label: "Demo Persona",
    options: {
      bu_sari: "Bu Sari's Family (4 members, Rp 60k/day)",
      anggaran_ekstrem: "Extreme Budget (5 members, Rp 25k/day)",
      mbg_sppg: "MBG SPPG (1 student, Rp 12k/day)",
    },
  },
  cta: {
    optimize: "Calculate Plan",
    optimizing: "Calculating...",
    reset: "Reset",
  },
  plans: {
    cheapest: "Cheapest",
    balanced: "Most Balanced",
    diverse: "Most Varied",
    relaxedBadge: "Target slightly relaxed",
    foodGroupCount: (n: number) => `${n} food groups`,
    totalCost: "Total Cost",
    relaxationReason: {
      budget_exhausted: "Budget too tight for further substitutions.",
      akg_bound_violated: "Variety limited by RDA constraints.",
      no_unused_food_groups: "All food groups are already in use.",
      underlying_cheapest_infeasible: "Base plan is infeasible.",
    } as Record<string, string>,
  },
  akg: {
    nutrient: {
      energy_kcal: "Energy",
      protein_g: "Protein",
      fat_g: "Fat",
      carbohydrate_g: "Carbs",
      iron_mg: "Iron",
      zinc_mg: "Zinc",
      vitamin_a_ug_rae: "Vitamin A",
      calcium_mg: "Calcium",
    } as Record<string, string>,
  },
  infeasibility: {
    title: "Current Budget Is Not Enough",
    minimumLabel: "Estimated minimum budget",
    deficitLabel: "Nutrients not met",
    raiseBudget: "Raise to minimum budget",
    restrictionsTitle: "Restrictions Are Too Strict",
    restrictionsHint: "Try loosening restrictions so a feasible ingredient mix exists.",
  },
  sensitivity: {
    title: "Price Scenario (What-If)",
    subtitle: "Drag the percentage to see the cost impact.",
    presets: {
      cabai_50: "Chili +50%",
      telur_minus10: "Eggs −10%",
    },
    deltaCost: (delta: number) => {
      const sign = delta > 0 ? "+" : delta < 0 ? "−" : "";
      const abs = Math.abs(delta);
      return `Δ Cost: ${sign}Rp ${abs.toLocaleString("id-ID")}`;
    },
  },
  drawer: {
    closeLabel: "Close",
    methodLabel: "Method",
    titlePrefix: "Recipe:",
    ingredients: "Ingredients",
  },
  errors: {
    generic: "Something went wrong. Please try again in a moment.",
    network: "Cannot reach the server. Please check your connection.",
    validation: "Please review your inputs.",
  },
  empty: {
    hero: "Fill in your family, set a budget, and press Calculate Plan to start.",
  },
  meals: {
    sarapan: "Breakfast",
    makan_siang: "Lunch",
    makan_malam: "Dinner",
    kudapan: "Snack",
  } as Record<string, string>,
  akgCategoryLabel: {
    toddler_1_3: "Toddler 1-3 yrs",
    child_4_6: "Child 4-6 yrs",
    teen_male_13_15: "Teen Male 13-15",
    teen_female_13_15: "Teen Female 13-15",
    adult_male_19_49: "Adult Male 19-49",
    adult_female_19_49: "Adult Female 19-49",
    lactating_mother_0_6m: "Lactating Mother (0-6m)",
  } as Record<string, string>,
};
